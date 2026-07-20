import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Each connected Google account has its own token file. token.json is the primary
# account; token_school.json (optional) is added via auth_google_school.py.
ACCOUNTS = [("token.json", "Personal"), ("token_school.json", "School")]

# SAFETY: Gmail access is READ-ONLY. The send and compose/draft-write scopes are
# deliberately excluded so this app is incapable of sending or altering mail at the
# Google API level, even if application code is changed. To fully enforce this,
# re-authorize token.json so it no longer carries gmail.send / gmail.compose.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

def get_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("gmail", "v1", credentials=creds)

def _gmail_services():
    """A (label, service) pair for every connected account whose token exists."""
    out = []
    for token_file, label in ACCOUNTS:
        if os.path.isfile(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            out.append((label, build("gmail", "v1", credentials=creds)))
    return out

def fetch_recent_emails(max_results=15) -> list:
    emails = []
    for label, service in _gmail_services():
        try:
            result = service.users().messages().list(
                userId="me", maxResults=max_results, labelIds=["INBOX"]
            ).execute()
        except Exception:
            continue  # one account failing shouldn't block the others
        for msg in result.get("messages", []):
            full = service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
            emails.append({
                "id": msg["id"],
                "account": label,
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", "unknown"),
                "date": headers.get("Date", "unknown"),
                "snippet": full.get("snippet", ""),
                "body": _extract_body(full["payload"])[:2000],  # cap tokens
            })
    return emails

def _extract_body(payload) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""

def format_emails_for_model(emails: list) -> str:
    if not emails:
        return "No recent emails found."
    lines = []
    for i, e in enumerate(emails, 1):
        lines.append(
            f"[{i}] ({e.get('account', 'Personal')} account) From: {e['from']}\n"
            f"    Subject: {e['subject']}\n"
            f"    Date: {e['date']}\n"
            f"    Body: {e['body'] or e['snippet']}\n"
        )
    return "\n".join(lines)

# SAFETY: Sending and Gmail-draft creation are intentionally NOT implemented.
# These stubs exist only to hard-fail if any code ever tries to call them, so a
# send path cannot be reintroduced by accident. Drafts live as text the user
# reviews and sends manually — nothing leaves this app.
def send_email(*args, **kwargs):
    raise RuntimeError("SENDING DISABLED: this app can never send email. Drafts are review-only.")

def create_draft(*args, **kwargs):
    raise RuntimeError("DISABLED: this app has read-only Gmail access and cannot write to Gmail.")
