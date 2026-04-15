"""Shared configuration for SmartHire application."""
import os

# MongoDB Configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/smarthire")
DB_NAME = "smarthire"

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "smarthire-secret-key-change-in-production")
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

# Judge0 API Configuration (no longer used — now using local execution)
# Kept for backward compatibility if you want to switch back to Judge0 later
JUDGE0_API_URL = "https://judge0-ce.p.rapidapi.com"
JUDGE0_API_KEY = ""
JUDGE0_API_HOST = "judge0-ce.p.rapidapi.com"

# Ollama Configuration
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")

# Scoring Weights
APTITUDE_WEIGHT = 0.3
CODING_WEIGHT = 0.4
INTERVIEW_WEIGHT = 0.3

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
