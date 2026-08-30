"""From-disk Google Drive upload/replace. Never inline file bytes into MCP args."""

from __future__ import annotations

import os
from pathlib import Path


DRIVE_FOLDER_ID = "1GebY2TnV4gbWhDfJQu-CV2lRPCH1mr-a"
CSV_MIME = "text/csv"
JSON_MIME = "application/json"


class DriveCredentialsMissing(RuntimeError):
    """Raised when no Google Drive credentials are available for API upload."""


def _build_credentials():
    """Return Google credentials if already present; never start OAuth or invent tokens."""
    token = os.environ.get("GOOGLE_DRIVE_TOKEN", "").strip()
    if token:
        try:
            from google.oauth2.credentials import Credentials
        except ImportError as exc:
            raise DriveCredentialsMissing(
                "GOOGLE_DRIVE_TOKEN is set but google-auth is not installed. "
                "pip install google-auth google-api-python-client"
            ) from exc
        return Credentials(token=token)

    try:
        import google.auth
    except ImportError as exc:
        raise DriveCredentialsMissing(
            "No GOOGLE_DRIVE_TOKEN and google-auth is not installed. "
            "Set GOOGLE_DRIVE_TOKEN or configure Application Default Credentials, "
            "or upload via the Drive web UI file picker from the local path."
        ) from exc

    try:
        credentials, _project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
    except Exception as exc:  # noqa: BLE001 — fail closed on any ADC miss
        raise DriveCredentialsMissing(
            "No Google Drive credentials available. "
            "Set GOOGLE_DRIVE_TOKEN (Bearer access token) or configure ADC "
            "(GOOGLE_APPLICATION_CREDENTIALS / gcloud application-default login). "
            "Do not pass file bytes through Drive MCP create_file. "
            "Upload from disk via the Drive web UI file picker, or retry after "
            "credentials are present."
        ) from exc
    return credentials


def _drive_service(credentials):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise DriveCredentialsMissing(
            "google-api-python-client is required for from-disk Drive upload. "
            "pip install google-api-python-client google-auth"
        ) from exc
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def find_file_id(title: str, parent_id: str = DRIVE_FOLDER_ID) -> str | None:
    """Return the newest non-trashed file id with exact title under parent, or None."""
    credentials = _build_credentials()
    service = _drive_service(credentials)
    query = (
        f"name = '{title.replace(chr(39), chr(92) + chr(39))}' "
        f"and '{parent_id}' in parents and trashed = false"
    )
    result = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=10,
        )
        .execute()
    )
    files = result.get("files") or []
    return files[0]["id"] if files else None


def upload_from_disk(
    path: str | Path,
    parent_id: str = DRIVE_FOLDER_ID,
    title: str | None = None,
    mime_type: str = CSV_MIME,
    file_id: str | None = None,
) -> dict:
    """Upload or replace a Drive file from a local path via MediaFileUpload.

    Bytes are read from disk by the Google API client (resumable/multipart).
    They must never be passed through MCP / CallDynamicTool JSON arguments.

    Requires GOOGLE_DRIVE_TOKEN or Application Default Credentials.
    Fails closed with DriveCredentialsMissing if neither is present.
    """
    local_path = Path(path)
    if not local_path.is_file():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    name = title or local_path.name
    credentials = _build_credentials()
    service = _drive_service(credentials)

    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise DriveCredentialsMissing(
            "google-api-python-client is required for from-disk Drive upload."
        ) from exc

    media = MediaFileUpload(
        str(local_path),
        mimetype=mime_type,
        resumable=True,
    )

    target_id = file_id
    if target_id is None:
        target_id = find_file_id(name, parent_id=parent_id)

    if target_id:
        updated = (
            service.files()
            .update(
                fileId=target_id,
                media_body=media,
                fields="id, name, mimeType, size, parents, webViewLink",
            )
            .execute()
        )
        return {"action": "updated", **updated}

    created = (
        service.files()
        .create(
            body={"name": name, "parents": [parent_id]},
            media_body=media,
            fields="id, name, mimeType, size, parents, webViewLink",
        )
        .execute()
    )
    return {"action": "created", **created}
