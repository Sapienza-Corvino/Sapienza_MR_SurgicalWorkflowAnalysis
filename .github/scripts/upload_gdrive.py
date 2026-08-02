import os
import sys
import json
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials as SACredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def is_ci_environment():
    """Restituisce True se l'ambiente non e interattivo (es. GitHub Actions)."""
    return os.environ.get("GITHUB_ACTIONS") == "true" or not sys.stdin.isatty()

def upload_zip():
    folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    
    # 1. Nome file ZIP configurabile tramite Secret GDRIVE_ZIP_FILENAME (default: MR_SurgicalWorkflowAnalysis.zip)
    target_filename = os.environ.get("GDRIVE_ZIP_FILENAME", "MR_SurgicalWorkflowAnalysis.zip").strip()
    if not target_filename:
        target_filename = "MR_SurgicalWorkflowAnalysis.zip"
    if not target_filename.endswith(".zip"):
        target_filename += ".zip"

    zip_path = os.environ.get("ZIP_FILE_PATH", target_filename)

    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN")
    client_id = os.environ.get("GDRIVE_CLIENT_ID")
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET")
    sa_json_str = os.environ.get("GDRIVE_SA_JSON")

    if not folder_id:
        print("[ERRORE] GDRIVE_FOLDER_ID mancante nei Secret/Env.")
        sys.exit(1)

    if refresh_token and client_id and client_secret:
        print("Autenticazione tramite OAuth User Refresh Token...")
        creds = OAuthCredentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        )
    elif sa_json_str:
        print("Autenticazione tramite Service Account JSON...")
        sa_info = json.loads(sa_json_str)
        creds = SACredentials.from_service_account_info(
            sa_info, scopes=["https://www.googleapis.com/auth/drive"]
        )
    else:
        print("[ERRORE] Credenziali mancanti (OAuth token o Service Account JSON richiesti).")
        sys.exit(1)

    service = build("drive", "v3", credentials=creds)

    print(f"Nome file ZIP di destinazione: '{target_filename}'")

    # 2. Elimina la precedente versione del file zip con lo stesso identico nome
    query_exact = f"'{folder_id}' in parents and name = '{target_filename}' and trashed = false"
    results_exact = service.files().list(
        q=query_exact,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    exact_files = results_exact.get("files", [])
    for f in exact_files:
        print(f"Eliminazione precedente versione dello zip (ID: {f['id']})...")
        service.files().delete(fileId=f['id'], supportsAllDrives=True).execute()

    # 3. Controllo di ALTRI file .zip presenti nella cartella di destinazione (se il nome del file e cambiato)
    query_other_zips = f"'{folder_id}' in parents and mimeType = 'application/zip' and name != '{target_filename}' and trashed = false"
    results_other = service.files().list(
        q=query_other_zips,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    other_zip_files = results_other.get("files", [])

    if other_zip_files:
        print(f"\n[AVVISO] Trovati {len(other_zip_files)} altri file .zip con nome diverso nella cartella di destinazione:")
        
        if is_ci_environment():
            # In GitHub Actions (CI): pulizia automatica per evitare accumulo di vecchi zip rinominati
            auto_clean = os.environ.get("GDRIVE_CLEAN_OTHER_ZIPS", "true").lower() == "true"
            for f in other_zip_files:
                if auto_clean:
                    print(f"  -> [CI AUTO-CLEAN] Eliminazione zip obsoleto: '{f['name']}' (ID: {f['id']})...")
                    service.files().delete(fileId=f['id'], supportsAllDrives=True).execute()
                else:
                    print(f"  -> [CI KEEP] Rilevato zip con nome diverso conservato: '{f['name']}'")
        else:
            # In ambiente locale interattivo: chiedi conferma all'utente uno ad uno (Y/n)
            for f in other_zip_files:
                ans = input(f"Vuoi eliminare il file zip obsoleto '{f['name']}' (ID: {f['id']})? [Y/n]: ").strip().lower()
                if ans == '' or ans.startswith('y') or ans == 's':
                    print(f"  -> Eliminazione '{f['name']}' in corso...")
                    service.files().delete(fileId=f['id'], supportsAllDrives=True).execute()
                else:
                    print(f"  -> File '{f['name']}' conservato.")

    # 4. Upload del nuovo file ZIP
    file_metadata = {
        'name': target_filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(zip_path, mimetype='application/zip', resumable=False)
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
    ).execute()

    print(f"\n✅ Upload completato con successo! File ZIP: '{target_filename}' (Drive ID: {uploaded_file.get('id')})")

if __name__ == "__main__":
    upload_zip()
