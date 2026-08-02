"""
Script di utilità locale per ottenere il GDRIVE_REFRESH_TOKEN.
"""
import os
import sys
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

def copy_to_clipboard(text):
    """Copia il testo negli appunti di Windows usando la utility nativa clip.exe."""
    try:
        if sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
            return True
    except Exception:
        pass
    return False

def run_oauth_flow(client_id, client_secret):
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    return flow.run_local_server(port=0)

def main():
    print("\n=======================================================")
    print("   GENERATORE GDRIVE_REFRESH_TOKEN PER GITHUB ACTIONS")
    print("=======================================================\n")

    client_id = os.environ.get("GDRIVE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET", "").strip()

    creds = None

    # Tentativo 1: usa credenziali pre-configurate nelle variabili d'ambiente se presenti
    if client_id and client_secret:
        print("-> Rilevate credenziali pre-configurate nelle variabili d'ambiente.")
        try:
            creds = run_oauth_flow(client_id, client_secret)
        except Exception as e:
            print(f"\n[AVVISO] Impossibile autenticarsi con le credenziali pre-configurate: {e}")
            print("-> Passaggio all'inserimento manuale...\n")

    # Tentativo 2: inserimento manuale se le variabili d'ambiente mancano o hanno dato errore
    if not creds:
        client_id = input("Incolla il tuo Client ID: ").strip()
        client_secret = input("Incolla il tuo Client Secret: ").strip()

        if not client_id or not client_secret:
            print("\n[ERRORE] Client ID e Client Secret sono obbligatori.")
            sys.exit(1)

        try:
            creds = run_oauth_flow(client_id, client_secret)
        except Exception as e:
            print(f"\n[ERRORE durante l'autenticazione] {e}")
            sys.exit(1)

    refresh_token = creds.refresh_token

    # Copia automatica negli appunti
    copied = copy_to_clipboard(refresh_token)

    print("\n=======================================================")
    print("           AUTORIZZAZIONE RIUSCITA CON SUCCESSO!")
    print("=======================================================")
    print("Ecco il tuo token per i Secret di GitHub:")
    print(f"\nGDRIVE_REFRESH_TOKEN = {refresh_token}\n")

    if copied:
        print("📋 [APPUNTI COPIATI] Il GDRIVE_REFRESH_TOKEN e stato COPIATO AUTOMATICAMENTE negli appunti!")
        print("   Puoi incollarlo direttamente (Ctrl+V) nei Secret del tuo repo GitHub.")
    else:
        print("   Seleziona e copia manualmente il token qui sopra.")

    print("=======================================================\n")

if __name__ == "__main__":
    main()
