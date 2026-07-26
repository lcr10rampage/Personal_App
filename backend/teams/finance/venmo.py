"""Venmo notification email -> budget. READ-ONLY Gmail (via the shared gmail_client,
which has no send path). Parsing is deterministic and conservative; de-duplication
prevents double entry across runs.
"""
import os
import re
import json
from email.utils import parsedate_to_datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(_HERE, ".venmo_processed.json")
VENMO_LOG_TAB = "Venmo"
LOG_HEADER = ["Date", "Direction", "Amount", "Counterparty", "Note", "Category", "MsgID"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

_AMOUNT_RE = re.compile(r"\$\s?([\d,]+\.\d{2})")


# ---------- parsing (pure, deterministic) ----------

def parse_venmo_email(subject: str, body: str) -> dict | None:
    """Parse a Venmo notification. Returns {amount, direction, counterparty, note} or
    None when it can't confidently read an amount + direction (skip, don't guess)."""
    text = subject or ""
    low = text.lower()
    m = _AMOUNT_RE.search(text) or _AMOUNT_RE.search(body or "")
    if not m:
        return None
    amount = float(m.group(1).replace(",", ""))

    if "paid you" in low or "you received" in low:
        direction = "received"
    elif "you paid" in low or "charged you" in low or "you sent" in low:
        direction = "paid"
    else:
        return None  # ambiguous direction — skip rather than misclassify

    counterparty = ""
    for pat in (r"you paid (.+?) \$", r"(.+?) paid you \$", r"(.+?) charged you \$"):
        mm = re.search(pat, text, re.I)
        if mm:
            counterparty = mm.group(1).strip()
            break

    note = ""
    mn = re.search(r"(?:note|for)[:\s]+(.{1,80})", body or "", re.I)
    if mn:
        note = mn.group(1).strip().splitlines()[0]

    return {"amount": amount, "direction": direction, "counterparty": counterparty, "note": note}


# ---------- de-duplication ----------

def load_processed() -> set:
    if os.path.isfile(PROCESSED_PATH):
        try:
            return set(json.load(open(PROCESSED_PATH)))
        except Exception:
            return set()
    return set()


def mark_processed(ids) -> None:
    cur = load_processed()
    cur.update(ids)
    json.dump(sorted(cur), open(PROCESSED_PATH, "w"))


# ---------- fetch new transactions ----------

def fetch_new(since_days: int = 30, max_results: int = 50) -> list[dict]:
    from agents.email.gmail_client import search_emails
    emails = search_emails(f"from:venmo@venmo.com newer_than:{since_days}d", max_results)
    processed = load_processed()
    out = []
    for e in emails:
        if e["id"] in processed:
            continue
        parsed = parse_venmo_email(e.get("subject", ""), e.get("body", ""))
        if not parsed:
            continue
        month, iso = None, e.get("date", "")
        try:
            dt = parsedate_to_datetime(e["date"])
            month, iso = MONTHS[dt.month - 1], dt.date().isoformat()
        except Exception:
            pass
        out.append({"msg_id": e["id"], "date": iso, "month": month, **parsed})
    return out


# ---------- money helpers ----------

def _money(s: str) -> float:
    s = (s or "").strip()
    if not s:
        return 0.0
    neg = s.startswith("(") or s.lstrip().startswith("-")
    digits = re.sub(r"[^\d.]", "", s)
    if not digits:
        return 0.0
    v = float(digits)
    return -v if neg else v


def _fmt(v: float) -> str:
    return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"


def signed(txn: dict) -> float:
    """Expenses (you paid) are negative in the budget grid; received is positive."""
    return -txn["amount"] if txn["direction"] == "paid" else txn["amount"]


# ---------- grid location ----------

def _locate(grid: list[list[str]]) -> dict:
    header_row = None
    for i, row in enumerate(grid):
        if any((c or "").strip() in MONTHS for c in row):
            header_row = i
            break
    month_cols, cat_rows = {}, {}
    if header_row is not None:
        for c, cell in enumerate(grid[header_row]):
            name = (cell or "").strip()
            if name in MONTHS:
                month_cols[name] = c
        for i in range(header_row + 1, len(grid)):
            name = (grid[i][0] or "").strip() if grid[i] else ""
            if name:
                cat_rows[name.lower()] = i
    return {"header_row": header_row, "month_cols": month_cols, "cat_rows": cat_rows}


# ---------- import: log + roll-up ----------

def _ensure_log_tab(sheets) -> None:
    try:
        sheets._sheet_id_for(VENMO_LOG_TAB)
    except Exception:
        sheets.add_sheet(VENMO_LOG_TAB)
        sheets.write_range(f"{VENMO_LOG_TAB}!A1", [LOG_HEADER])


def import_transactions(sheets, budget_range: str, transactions: list[dict]) -> dict:
    """Log each transaction to the Venmo tab AND roll it into the budget grid.
    Conservative: unknown month column -> log only, skip roll-up (reported)."""
    _ensure_log_tab(sheets)

    # If anything needs Uncategorized and the row is missing, create it once, then re-read.
    grid = sheets.read_range(budget_range)
    loc = _locate(grid)
    needs_uncat = any((t.get("category") or "Uncategorized").lower() not in loc["cat_rows"]
                      for t in transactions)
    if needs_uncat and "uncategorized" not in loc["cat_rows"]:
        sheets.append_rows([["Uncategorized"]])
        grid = sheets.read_range(budget_range)
        loc = _locate(grid)

    logged, rolled, skipped = 0, 0, []
    done_ids = []
    for t in transactions:
        cat = (t.get("category") or "Uncategorized").strip()
        # audit log row (always)
        sheets.append_rows([[t.get("date", ""), t["direction"], f"${t['amount']:.2f}",
                             t.get("counterparty", ""), t.get("note", ""), cat,
                             t.get("msg_id", "")]], VENMO_LOG_TAB)
        logged += 1

        month = t.get("month")
        col = loc["month_cols"].get(month) if month else None
        row = loc["cat_rows"].get(cat.lower())
        if row is None:
            row = loc["cat_rows"].get("uncategorized")
        if col is None or row is None:
            skipped.append(f"{t.get('counterparty','?')} ${t['amount']:.2f} "
                           f"(no {'month column for '+str(month) if col is None else 'category row'})")
        else:
            current = grid[row][col] if col < len(grid[row]) else ""
            newv = _money(current) + signed(t)
            a1 = f"{sheets._index_to_col(col)}{row + 1}"
            sheets.write_cell(a1, _fmt(newv))
            rolled += 1
        done_ids.append(t.get("msg_id"))

    mark_processed([i for i in done_ids if i])
    return {"logged": logged, "rolled_up": rolled, "skipped_rollup": skipped}
