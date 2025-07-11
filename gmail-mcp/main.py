import os
from fastmcp import FastMCP, tool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

mcp = FastMCP("Gmail MCP Server")

@mcp.tool()
def fetch_unread_emails(max_results: int = 5):
    """
    Fetch unread emails from Gmail.
    """
    service = get_gmail_service()
    results = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
        snippet = msg_data.get("snippet", "")
        emails.append({
            "id": msg["id"],
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "snippet": snippet,
        })
    return emails

@mcp.tool()
def send_email(to: str, subject: str, body: str):
    """
    Send an email via Gmail.
    """
    import base64
    from email.mime.text import MIMEText

    service = get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw}
    sent = service.users().messages().send(userId="me", body=message_body).execute()
    return {"id": sent["id"], "status": "sent"}

@mcp.tool()
def mark_email_processed(email_id: str):
    """
    Mark an email as processed by removing the UNREAD label and adding a 'Processed' label.
    """
    service = get_gmail_service()
    # Remove UNREAD label
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()
    # Optionally, add a custom 'Processed' label
    # First, get or create the label
    labels = service.users().labels().list(userId="me").execute().get('labels', [])
    processed_label_id = None
    for label in labels:
        if label['name'].lower() == 'processed':
            processed_label_id = label['id']
            break
    if not processed_label_id:
        label_obj = service.users().labels().create(
            userId="me",
            body={"name": "Processed", "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        ).execute()
        processed_label_id = label_obj['id']
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"addLabelIds": [processed_label_id]}
    ).execute()
    return {"id": email_id, "status": "processed"}

if __name__ == "__main__":
    mcp.run() 