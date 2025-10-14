import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
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

        self.DB_POOL_MIN_CONN = int(os.getenv("DB_POOL_MIN_CONN", "1"))
        self.DB_POOL_MAX_CONN = int(os.getenv("DB_POOL_MAX_CONN", "20"))

        # Cache for config data loaded from database
        self._config_cache: Dict[str, Any] = {}

    def get_capabilities_data(self) -> Optional[Dict[str, Any]]:
        """Load capabilities from database, fallback to local file"""
        if 'capabilities' in self._config_cache:
            return self._config_cache['capabilities']

        # Try database first
        try:
            from agent.database.db_manager import DatabaseManager
            db = DatabaseManager()
            config_data = db.get_config_file('capabilities')
            if config_data:
                self._config_cache['capabilities'] = config_data
                return config_data
        except Exception as e:
            print(f"⚠️ Could not load capabilities from database: {e}")

        # Fallback to local file
        try:
            config_dir = Path(__file__).parent
            local_path = config_dir / "capabilities.json"
            if local_path.exists():
                with open(local_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._config_cache['capabilities'] = config_data
                    return config_data
        except Exception as e:
            print(f"⚠️ Could not load capabilities from local file: {e}")

        return None

    def get_qualification_matrix(self) -> Optional[Dict[str, Any]]:
        """Load qualification matrix from database, fallback to local file"""
        if 'qualification_matrix' in self._config_cache:
            return self._config_cache['qualification_matrix']

        # Try database first
        try:
            from agent.database.db_manager import DatabaseManager
            db = DatabaseManager()
            config_data = db.get_config_file('qualification_matrix')
            if config_data:
                self._config_cache['qualification_matrix'] = config_data
                return config_data
        except Exception as e:
            print(f"⚠️ Could not load qualification matrix from database: {e}")

        # Fallback to local file
        try:
            config_dir = Path(__file__).parent
            local_path = config_dir / "qualification_matrix.json"
            if local_path.exists():
                with open(local_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._config_cache['qualification_matrix'] = config_data
                    return config_data
        except Exception as e:
            print(f"⚠️ Could not load qualification matrix from local file: {e}")

        return None

    def validate(self):
        """Validate that all required settings are present"""
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set in .env file")

        if not self.FILES_DIR.exists():
            raise ValueError(f"FILES_DIR does not exist: {self.FILES_DIR}")

        return True

settings = Settings()
