import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose"
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

def create_draft(to: str, subject: str, body: str) -> str:
    service = get_service()
    message_text = f"To: {to}\nSubject: {subject}\n\n{body}"
    encoded = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8")
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": encoded}}
    ).execute()
    return f"Draft created with ID: {draft['id']}"
