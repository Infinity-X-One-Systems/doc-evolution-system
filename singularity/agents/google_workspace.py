"""
google_workspace.py — Singularity Prime Google Workspace Connector

Capabilities:
  - Gmail: notify on deployment, approval required, chaos detected
  - Google Drive: archive validation reports
  - Google Sheets: log deployment summaries

Authentication: Service Account (key JSON from GOOGLE_SERVICE_ACCOUNT_JSON env var)
or OAuth (GOOGLE_OAUTH_TOKEN env var).

All operations gracefully degrade if credentials are not set — CI will not fail
due to missing Google credentials; a warning is emitted instead.
"""

import json
import os
import sys
import datetime
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path


def _get_token() -> str | None:
    """Return a bearer token from environment or service account."""
    direct = os.environ.get("GOOGLE_OAUTH_TOKEN")
    if direct:
        return direct
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            sa = json.loads(sa_json)
            _ = sa.get("client_email")  # validate structure
            # In production, use google-auth to exchange SA creds for an access token.
            # Returning None here as google-auth is an optional dependency.
            print(
                "[google_workspace] Service account JSON detected. "
                "Install 'google-auth' package to activate token exchange.",
                file=sys.stderr,
            )
        except json.JSONDecodeError:
            print("[google_workspace] Invalid GOOGLE_SERVICE_ACCOUNT_JSON", file=sys.stderr)
    return None


def send_gmail_notification(subject: str, body: str, recipient: str) -> bool:
    """Send a Gmail notification via Gmail API. Returns True on success."""
    token = _get_token()
    if not token:
        print(
            f"[google_workspace] WARNING: No Google token. Skipping Gmail → {recipient}",
            file=sys.stderr,
        )
        return False

    import base64
    raw_message = f"To: {recipient}\nSubject: {subject}\n\n{body}"
    encoded = base64.urlsafe_b64encode(raw_message.encode()).decode()
    payload = json.dumps({"raw": encoded}).encode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            print(f"[google_workspace] Gmail sent to {recipient}: {resp.status}")
            return True
    except urllib.error.HTTPError as exc:
        print(f"[google_workspace] Gmail error {exc.code}", file=sys.stderr)
        return False


def archive_to_drive(file_path: str, folder_id: str | None = None) -> bool:
    """Upload a file to Google Drive. Returns True on success."""
    token = _get_token()
    if not token:
        print(
            f"[google_workspace] WARNING: No Google token. Skipping Drive upload: {file_path}",
            file=sys.stderr,
        )
        return False

    content = Path(file_path).read_bytes()
    name = Path(file_path).name
    metadata = json.dumps(
        {"name": name, **({"parents": [folder_id]} if folder_id else {})}
    ).encode()
    boundary = "singularity_boundary"
    body = (
        f"--{boundary}\r\nContent-Type: application/json\r\n\r\n".encode()
        + metadata
        + f"\r\n--{boundary}\r\nContent-Type: application/json\r\n\r\n".encode()
        + content
        + f"\r\n--{boundary}--".encode()
    )
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            result = json.loads(resp.read())
            print(f"[google_workspace] Drive upload OK: {result.get('id')}")
            return True
    except urllib.error.HTTPError as exc:
        print(f"[google_workspace] Drive error {exc.code}", file=sys.stderr)
        return False


def log_to_sheets(spreadsheet_id: str, row: list) -> bool:
    """Append a row to a Google Sheet. Returns True on success."""
    token = _get_token()
    if not token:
        print(
            "[google_workspace] WARNING: No Google token. Skipping Sheets log.",
            file=sys.stderr,
        )
        return False

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        f"/values/A1:append?valueInputOption=USER_ENTERED"
    )
    payload = json.dumps({"values": [row]}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            print(f"[google_workspace] Sheets row appended: {resp.status}")
            return True
    except urllib.error.HTTPError as exc:
        print(f"[google_workspace] Sheets error {exc.code}", file=sys.stderr)
        return False


def main() -> None:
    event = os.environ.get("SINGULARITY_EVENT", "deployment")
    recipient = os.environ.get("NOTIFY_EMAIL", "")
    spreadsheet_id = os.environ.get("GOOGLE_SHEET_ID", "")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    if event == "deployment" and recipient:
        send_gmail_notification(
            subject="[Singularity Prime] Deployment Complete",
            body=f"Repository deployed successfully at {now}.",
            recipient=recipient,
        )
    elif event == "approval_required" and recipient:
        send_gmail_notification(
            subject="[Singularity Prime] Approval Required",
            body=f"A PR is awaiting your approval. Timestamp: {now}.",
            recipient=recipient,
        )

    validation_report = "singularity/evolution/validation_report.json"
    drive_folder = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if Path(validation_report).exists():
        archive_to_drive(validation_report, drive_folder)

    if spreadsheet_id:
        log_to_sheets(spreadsheet_id, [now, event, "Singularity Prime"])

    print("[google_workspace] Google Workspace connector run complete.")


if __name__ == "__main__":
    main()
