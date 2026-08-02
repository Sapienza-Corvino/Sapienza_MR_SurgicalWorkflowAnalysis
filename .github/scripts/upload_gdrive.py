import os
import sys
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_zip():
    folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    sa_json_str = os.environ.get("GDRIVE_SA_JSON")
    zip_path = os.environ.get("ZIP_FILE_PATH", "MR_SurgicalWorkflowAnalysis.zip")
    target_filename = "MR_SurgicalWorkflowAnalysis.zip"

    if not folder_id or not sa_json_str:
        print("Error: GDRIVE_FOLDER_ID or GDRIVE_SA_JSON missing.")
        sys.exit(1)

    sa_info = json.loads(sa_json_str)
    creds = Credentials.from_service_account_info(
        sa_info, scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    # Search existing zip in folder and delete it
    query = f"'{folder_id}' in parents and name = '{target_filename}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    for f in files:
        print(f"Deleting previous file (ID: {f['id']})...")
        service.files().delete(fileId=f['id']).execute()

    # Upload new file
    file_metadata = {
        'name': target_filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(zip_path, mimetype='application/zip', resumable=True)
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"Upload completed successfully! Drive File ID: {uploaded_file.get('id')}")

if __name__ == "__main__":
    upload_zip()
