from google_auth_oauthlib.flow import Flow
import json

# Gmail is READ-ONLY on purpose: no compose/send scope, so this app's token is
# incapable of sending or drafting mail at the Google level (the finance Venmo import
# and the email manager both only ever read). Calendar keeps write (events) access.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
]

flow = Flow.from_client_secrets_file(
    "credentials.json",
    scopes=SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)

auth_url, _ = flow.authorization_url(prompt="consent")

print("\nVisit this URL in your browser:")
print(auth_url)
print()

code = input("Paste the code from Google here: ")
flow.fetch_token(code=code)

with open("token.json", "w") as f:
    f.write(flow.credentials.to_json())

print("\nDone! token.json saved.")
