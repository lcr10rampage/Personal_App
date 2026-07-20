import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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

def fetch_recent_emails(max_results=15) -> list:
    service = get_service()
    result = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"]
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "unknown")
        date = headers.get("Date", "unknown")
        snippet = full.get("snippet", "")
        body = _extract_body(full["payload"])

        emails.append({
            "id": msg["id"],
            "subject": subject,
            "from": sender,
            "date": date,
            "snippet": snippet,
            "body": body[:2000]  # cap body length to control tokens
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
            f"[{i}] From: {e['from']}\n"
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
