from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)

results = service.files().list(
    q="'15X-_JQZIqaqWHlmNV9NSEQUNdz3-FtG6' in parents"
).execute()

print(results)