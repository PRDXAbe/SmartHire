# SmartHire Local setup

SmartHire runs on one machine at `http://127.0.0.1:5000`. It does not require a cloud service, API key, database server, or deployment.

## 1. Get the source

```bash
git clone https://github.com/PRDXAbe/Smarthire.git
cd Smarthire
```

## 2. Install Python dependencies

Use Python 3.11 or 3.12. A virtual environment is recommended.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r app\requirements.txt
```

### macOS, Linux, Git Bash, or WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt
```

## 3. Add optional local models

The repository deliberately excludes `app/models/` because it contains large model files and model redistribution must be reviewed separately.

- Resume screening, job templates, example resumes, aptitude, coding, reports, and typed interviews work without model files.
- Local speech transcription needs the bundled Faster Whisper model under `app/models/models--Systran--faster-whisper-base/`.
- Camera face comparison needs `app/models/face/face_recognition_sface_2021dec.onnx` and `app/models/face/face_landmarker.task`.

Copy approved local model files into those paths before using those features. The app stays offline after its dependencies and models are installed.

## 4. Start the application

### Windows

Double-click `START_SMARTHIRE.cmd`, or run:

```powershell
.\START_SMARTHIRE.cmd
```

### macOS, Linux, Git Bash, or WSL

```bash
chmod +x start_smarthire.sh
./start_smarthire.sh
```

Open `http://127.0.0.1:5000`.

## 5. Verify the source checkout

```bash
cd app
python -m unittest unified.test_app -v
```

The SQLite file at `app/unified/smarthire.sqlite3` contains local candidate records and is intentionally ignored by Git. Do not commit it.
