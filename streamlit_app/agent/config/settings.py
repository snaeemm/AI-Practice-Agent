import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")

        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in .env file")

        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025")

        self.FILES_DIR = Path(os.getenv("FILES_DIR", "./related_files")).resolve()
        self.RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "./results")).resolve()
        self.OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output")).resolve()

        # self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        # Config files always use agent/config/ directory (deployment-agnostic)
        config_dir = Path(__file__).parent
        self.CAPABILITIES_JSON = config_dir / "capabilities.json"
        self.QUALIFICATION_JSON = config_dir / "qualification_matrix.json"

        self.DB_POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN_CONN", "1"))
        self.DB_POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX_CONN", "20"))

    def validate(self):
        """Validate that all required settings are present"""
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set in .env file")

        if not self.FILES_DIR.exists():
            raise ValueError(f"FILES_DIR does not exist: {self.FILES_DIR}")

        return True

settings = Settings()
