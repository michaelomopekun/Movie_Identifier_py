from io import BytesIO
from pathlib import Path
import zipfile
import requests
import shutil
import os
from datetime import datetime

class DbManager:

    def __init__(self):
        self.parent_dir = Path(__file__).resolve().parent.parent
        self.CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", self.parent_dir / "chroma_db"))
        self.BACKUP_DIR = Path(os.getenv("BACKUP_DIR", self.parent_dir / "db_backups"))
        self.NEW_DB_ZIP_URL = os.getenv("NEW_DB_ZIP_URL")

    def backup_current_db(self):
        if self.CHROMA_DB_PATH.exists():
            self.BACKUP_DIR.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.BACKUP_DIR / f"chroma_db_backup_{timestamp}"
            shutil.copytree(self.CHROMA_DB_PATH, backup_path)
            print(f"📁 DB backed up to {backup_path}")

    def delete_existing_chromadb(self):
        if self.CHROMA_DB_PATH.exists():
            shutil.rmtree(self.CHROMA_DB_PATH)

    def download_chromadb_zip(self, url: str = None) -> BytesIO:
        url = url or self.NEW_DB_ZIP_URL
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to download new DB")
        return BytesIO(response.content)

    def extract_zip_to_path(self, zip_bytes: BytesIO):
        with zipfile.ZipFile(zip_bytes) as zip_ref:
            zip_ref.extractall(self.CHROMA_DB_PATH)

    def update_chromadb(self, zip_url: str = None):
        print("📦 Backing up existing DB...")
        self.backup_current_db()

        print("🗑️ Deleting old DB...")
        self.delete_existing_chromadb()

        print("⬇️ Downloading new DB...")
        zip_bytes = self.download_chromadb_zip(zip_url)

        print("📦 Extracting new DB...")
        self.extract_zip_to_path(zip_bytes)

        print("✅ DB update complete.")

dbManager = DbManager()
