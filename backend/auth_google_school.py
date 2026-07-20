"""Authorize a SECOND Google account (your school account) as READ-ONLY.

Run:  python auth_google_school.py
It prints a URL — open it, sign in with your SCHOOL Google account, approve, paste the
code back. It writes token_school.json, which the app reads alongside token.json.

SAFETY: only read-only scopes are requested — this account can never send email or change
your calendar. It is used purely to read your school inbox and calendar.
"""
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]

flow = Flow.from_client_secrets_file(
    "credentials.json",
    scopes=SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob",
)

auth_url, _ = flow.authorization_url(prompt="consent")

print("\n1. Open this URL and sign in with your SCHOOL Google account:")
print("\n" + auth_url + "\n")

code = input("2. Paste the code from Google here: ").strip()
flow.fetch_token(code=code)

with open("token_school.json", "w") as f:
    f.write(flow.credentials.to_json())

print("\nDone! token_school.json saved. Your school account is now connected (read-only).")
