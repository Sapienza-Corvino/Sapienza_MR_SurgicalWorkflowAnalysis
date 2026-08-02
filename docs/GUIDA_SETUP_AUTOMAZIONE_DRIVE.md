# Guida Completa Setup Automazione GitHub Actions -> Google Drive

**Progetto:** Surgical Workflow Analysis — Medical Robotics Project  
**Istituzione:** Sapienza Università di Roma (Luglio 2026)  
**Documento di riferimento:** Specifiche di configurazione per il caricamento automatico dello ZIP del repository su Google Drive ad ogni `git push`.

---

## 📌 1. Obiettivo e Motivazione Tecnica

### Obiettivo

Consentire ai compagni di gruppo (che non possiedono un account GitHub o che non devono accedere direttamente al repository privato) di scaricare sempre la versione più aggiornata del codice e della documentazione in formato `.zip` tramite un **semplice link Google Drive condiviso**, senza rendere il repository GitHub pubblico.

### Perché si usa l'OAuth Refresh Token anziché il Service Account?

* **Problema del Service Account:** I Service Account di Google Cloud hanno per regola nativa una quota di archiviazione personale di **0 MB**. Quando un Service Account tenta di creare un file dentro *"Il mio Drive"* (anche se la cartella è condivisa), Google blocca il caricamento con l'errore `403: Service Accounts do not have storage quota`.
* **Soluzione OAuth:** L'autenticazione tramite **OAuth 2.0 Refresh Token** fa sì che la GitHub Action esegua il caricamento **autenticandosi per conto del tuo account utente Sapienza** (`@studenti.uniroma1.it`). In questo modo l'upload sfrutta lo spazio di archiviazione del tuo account Google Sapienza (senza limiti di quota da Service Account) e funziona in qualsiasi cartella di *"Il mio Drive"* o *"Condivisi con me"*.

---

## 🛠️ 2. Architettura dei File del Progetto

Tutti i file dell'automazione sono stati predisposti nel repository senza chiavi sensibili hardcoded:

1. **[`.github/workflows/upload_to_gdrive.yml`](file:///C:/Users/chris/Desktop/MR_SurgicalWorkflowAnalysis/.github/workflows/upload_to_gdrive.yml)**:
   Workflow di GitHub Actions che scatta ad ogni `git push` sul ramo `main` (o `master`). Legge il nome dello zip dal Secret opzionale `GDRIVE_ZIP_FILENAME` (o usa il default `MR_SurgicalWorkflowAnalysis.zip`), genera l'archivio ZIP con `git archive` ed esegue lo script di upload.

2. **[`.github/scripts/upload_gdrive.py`](file:///C:/Users/chris/Desktop/MR_SurgicalWorkflowAnalysis/.github/scripts/upload_gdrive.py)**:
   Script Python eseguito dalla GitHub Action. Legge le credenziali dai Secret di GitHub:
   * Elimina la versione precedente dello ZIP con nome identico.
   * **Gestione vecchi ZIP rinominati**: Cerca eventuali altri file `.zip` nella cartella destinazione. In ambiente GitHub Actions (non-interattivo) effettua la pulizia automatica per evitare l'accumulo di vecchi zip rinominati; in esecuzione locale chiede conferma interattiva file per file `[Y/n]`.
   * Carica il nuovo archivio `.zip`.

3. **[`src/tools/get_oauth_token.py`](file:///C:/Users/chris/Desktop/MR_SurgicalWorkflowAnalysis/src/tools/get_oauth_token.py)**:
   Script Python locale per il flusso di autenticazione OAuth. Supporta il fallback automatico e **copia automaticamente il Refresh Token negli appunti di Windows**.

4. **[`config/setup_oauth_token.bat`](file:///C:/Users/chris/Desktop/MR_SurgicalWorkflowAnalysis/config/setup_oauth_token.bat)**:
   Script Batch per Windows che automatizza il setup locale.

5. **[`.gitignore`](file:///C:/Users/chris/Desktop/MR_SurgicalWorkflowAnalysis/.gitignore)**:
   Ignora l'ambiente virtuale temporaneo `config/.venv_oauth/`, tracciando i file di configurazione puliti.

---

## 🚀 3. Guida Passo-Passo per la Configurazione

### PASSO 1: Creazione delle credenziali su Google Cloud Console

1. Accedi a [Google Cloud Console](https://console.cloud.google.com/) con il tuo profilo **Google Sapienza** (`@studenti.uniroma1.it`).
2. Seleziona o crea un progetto (es. `MR-Surgical-Workflow`).
3. Abilita la **Google Drive API**:
   * Vai alla pagina [Google Drive API Overview](https://console.developers.google.com/apis/api/drive.googleapis.com/overview) e clicca su **ABILITA** (ENABLE).
4. Configura la **Schermata di consenso OAuth** (se richiesta):
   * Tipo utente: **Esterno** (o *Interno*).
   * Nome App: `GitHub Drive Uploader`.
   * Email di supporto e dati di contatto: inserisci la tua email Sapienza.
   * Clicca su *Salva e continua* fino a completare la procedura.
5. Crea l'**ID Client OAuth**:
   * Vai su **Credenziali** $\rightarrow$ **+ Crea credenziali** $\rightarrow$ **ID client OAuth**.
   * Tipo di applicazione: **Applicazione desktop**.
   * Nome: `GitHub Uploader`.
   * Clicca su **Crea**.
6. Salva i due valori mostrati a schermo:
   * **`ID Client`** (es: `389441030713-3bl1f51asbc63kuu4c8jc6tjltmsojhn.apps.googleusercontent.com`)
   * **`Segreto Client`** (es: `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`)

---

### PASSO 2: Generazione del `GDRIVE_REFRESH_TOKEN` in locale

1. Sul tuo PC, apri la cartella del progetto ed esegui il file:

   ```cmd
   config\setup_oauth_token.bat
   ```

2. Incolla il **Client ID** e il **Client Secret**.
3. Si aprirà il browser: accedi con l'account **Google Sapienza** e seleziona *Consenti*.
4. **Copia automatica negli appunti:** Lo script copierà automaticamente il `GDRIVE_REFRESH_TOKEN` negli appunti di Windows!

---

### PASSO 3: Individuazione dell'ID della Cartella Google Drive (`GDRIVE_FOLDER_ID`)

1. Apri [Google Drive](https://drive.google.com/) con l'account Sapienza.
2. Apri la cartella destinazione.
3. Copia l'ID dall'URL della cartella:
   * Esempio URL: `https://drive.google.com/drive/u/1/folders/1fA9QgeKbwx_yzT9vbAyLY42jbzFD7rMu`
   * **ID Cartella (`GDRIVE_FOLDER_ID`):** `1fA9QgeKbwx_yzT9vbAyLY42jbzFD7rMu`

---

### PASSO 4: Inserimento dei Secret nel Repository GitHub

Nel tuo repository privato su GitHub.com:

1. Vai su **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** $\rightarrow$ **New repository secret**.
2. Configura i Secret:

| Nome Secret | Valore | Obbligatorio |
| :--- | :--- | :---: |
| **`GDRIVE_FOLDER_ID`** | L'ID estratto dall'URL della cartella Drive | Sì |
| **`GDRIVE_CLIENT_ID`** | L'ID Client OAuth generato su Google Cloud Console | Sì |
| **`GDRIVE_CLIENT_SECRET`** | Il Segreto Client OAuth generato su Google Cloud Console | Sì |
| **`GDRIVE_REFRESH_TOKEN`** | Il Refresh Token generato (già copiato negli appunti) | Sì |
| **`GDRIVE_ZIP_FILENAME`** | Nome personalizzato dello ZIP (es. `SurgicalWorkflow_Project.zip`) | No (Default: `MR_SurgicalWorkflowAnalysis.zip`) |

---

### PASSO 5: Esecuzione e Verifica

Nel terminale del progetto esegui il commit e il push:

```bash
git add .
git commit -m "Support custom zip filename secret and automated old zip cleanup"
git push origin main
```

Ad ogni push, GitHub Actions:

1. Genera lo `.zip` usando il nome specificato in `GDRIVE_ZIP_FILENAME` (o il nome di default).
2. Elimina la precedente versione dello zip con nome identico.
3. Se rileva altri file `.zip` nella cartella (risultanti da un precedente cambio di nome), li pulisce per mantenere la cartella ordinata.
4. Carica il nuovo archivio `.zip` aggiornato.
