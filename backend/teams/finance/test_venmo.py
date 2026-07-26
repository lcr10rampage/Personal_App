"""Offline tests for Venmo parsing + roll-up math. Run: python teams/finance/test_venmo.py
(from the backend dir). No network, no real sheet — uses an in-memory fake sheet."""
import re
import tempfile
from teams.finance import venmo


# ---------- parser ----------

def test_parse_paid_p2p():
    r = venmo.parse_venmo_email("You paid Cheston $5.36",
                                "Cheston paid Cheston Riley $ 5 . 36 River link tolls Like Comment")
    assert r["amount"] == 5.36 and r["direction"] == "paid" and r["counterparty"] == "Cheston"
    assert r["note"] == "River link tolls"


def test_parse_received():
    r = venmo.parse_venmo_email("You got $98.40 from Cheston", "Cheston paid you $ 98 . 40 Like Comment")
    assert r["amount"] == 98.4 and r["direction"] == "received" and r["counterparty"] == "Cheston"


def test_parse_debit_purchase():
    r = venmo.parse_venmo_email("You made a purchase with your debit card",
                                "You paid Five Guys Ga 1582 Qsr $23.38. Luke paid ...")
    assert r["amount"] == 23.38 and r["direction"] == "paid"
    assert r["counterparty"] == "Five Guys Ga 1582 Qsr"


def test_parse_html_entities_cleaned():
    r = venmo.parse_venmo_email("You made a purchase with your debit card",
                                "You paid Bantam &amp; Biddy $20.15.")
    assert r["counterparty"] == "Bantam & Biddy"


def test_parse_request_is_skipped():
    assert venmo.parse_venmo_email("Michelle requested $8.00", "Michelle requests $8.00") is None
    assert venmo.parse_venmo_email("Reminder: Cheston Riley requested $5.36", "") is None


def test_parse_declined_is_skipped():
    assert venmo.parse_venmo_email("Your payment to BUFFALO WILD was declined", "declined") is None


def test_parse_no_amount_returns_none():
    assert venmo.parse_venmo_email("Your Venmo statement is ready", "no amount here") is None


def test_money_helpers():
    assert venmo._money("-$38.75") == -38.75
    assert venmo._money("$100.00") == 100.0
    assert venmo._money("") == 0.0
    assert venmo._fmt(-20.0) == "-$20.00"
    assert venmo._fmt(12.5) == "$12.50"
    assert venmo.signed({"amount": 20, "direction": "paid"}) == -20
    assert venmo.signed({"amount": 20, "direction": "received"}) == 20


# ---------- fake sheet + roll-up ----------

class FakeSheets:
    def __init__(self, grid):
        self.tabs = {None: [row[:] for row in grid]}

    @staticmethod
    def _split(ref):
        return ref.split("!", 1) if "!" in ref else (None, ref)

    @staticmethod
    def _col(letters):
        idx = 0
        for ch in letters.upper():
            idx = idx * 26 + (ord(ch) - 64)
        return idx - 1

    @staticmethod
    def _index_to_col(idx):
        letters = ""
        idx += 1
        while idx:
            idx, rem = divmod(idx - 1, 26)
            letters = chr(65 + rem) + letters
        return letters

    def read_range(self, rng):
        tab, _ = self._split(rng)
        return self.tabs.get(tab, [])

    def write_cell(self, a1, value):
        tab, cell = self._split(a1)
        m = re.match(r"([A-Za-z]+)(\d+)", cell)
        col, row = self._col(m.group(1)), int(m.group(2)) - 1
        grid = self.tabs.setdefault(tab, [])
        while len(grid) <= row:
            grid.append([])
        while len(grid[row]) <= col:
            grid[row].append("")
        grid[row][col] = value

    def append_rows(self, values, sheet_title=None):
        self.tabs.setdefault(sheet_title, []).extend([v[:] for v in values])

    def add_sheet(self, title):
        self.tabs.setdefault(title, [])
        return 1

    def write_range(self, anchor, values):
        tab, cell = self._split(anchor)
        m = re.match(r"([A-Za-z]+)(\d+)", cell)
        col0, row0 = self._col(m.group(1)), int(m.group(2)) - 1
        grid = self.tabs.setdefault(tab, [])
        for r, rowvals in enumerate(values):
            row = row0 + r
            while len(grid) <= row:
                grid.append([])
            for c, val in enumerate(rowvals):
                cc = col0 + c
                while len(grid[row]) <= cc:
                    grid[row].append("")
                grid[row][cc] = val

    def _sheet_id_for(self, title):
        if title in self.tabs:
            return 1
        raise ValueError("no tab")


def _fresh_sheets():
    return FakeSheets([
        ["Expenses", "Amount", "Balance", "January", "February"],
        ["Groceries", "-50", "", "-30", ""],
        ["Eating out", "-100", "", "", ""],
    ])


def _isolate_dedup():
    venmo.PROCESSED_PATH = tempfile.mktemp(suffix=".json")


def test_rollup_known_category():
    _isolate_dedup()
    s = _fresh_sheets()
    r = venmo.import_transactions(s, "A1:E10", [{
        "msg_id": "m1", "month": "January", "amount": 20.0, "direction": "paid",
        "counterparty": "Cafe", "note": "", "category": "Eating out"}])
    assert r["logged"] == 1 and r["rolled_up"] == 1
    # Eating out (row idx 2 -> sheet row 3), January (col idx 3 -> 'D') = -$20.00
    assert s.tabs[None][2][3] == "-$20.00"


def test_rollup_sums_into_existing():
    _isolate_dedup()
    s = _fresh_sheets()
    venmo.import_transactions(s, "A1:E10", [{
        "msg_id": "m2", "month": "January", "amount": 20.0, "direction": "paid",
        "counterparty": "Store", "note": "", "category": "Groceries"}])
    # Groceries January started at -30, minus 20 = -50
    assert s.tabs[None][1][3] == "-$50.00"


def test_unknown_category_goes_to_uncategorized():
    _isolate_dedup()
    s = _fresh_sheets()
    venmo.import_transactions(s, "A1:E10", [{
        "msg_id": "m3", "month": "January", "amount": 10.0, "direction": "paid",
        "counterparty": "X", "note": "", "category": "Rocketry"}])
    # An 'Uncategorized' row was appended and rolled into.
    labels = [row[0] for row in s.tabs[None] if row]
    assert "Uncategorized" in labels


def test_missing_month_skips_rollup_but_logs():
    _isolate_dedup()
    s = _fresh_sheets()
    r = venmo.import_transactions(s, "A1:E10", [{
        "msg_id": "m4", "month": "March", "amount": 10.0, "direction": "paid",
        "counterparty": "Y", "note": "", "category": "Groceries"}])
    assert r["logged"] == 1 and r["rolled_up"] == 0 and r["skipped_rollup"]
    # It was still logged to the Venmo tab.
    assert len(s.tabs["Venmo"]) >= 2  # header + 1 row


def test_dedup_marks_processed():
    _isolate_dedup()
    s = _fresh_sheets()
    venmo.import_transactions(s, "A1:E10", [{
        "msg_id": "m5", "month": "January", "amount": 5.0, "direction": "paid",
        "counterparty": "Z", "note": "", "category": "Groceries"}])
    assert "m5" in venmo.load_processed()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)} passed")
