from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from Service.TrailerSearchService import TrailerSearchService
from models.response_model import SearchResult
from Service.db_manager import dbManager
from pathlib import Path
import datetime
import shutil
import os

router = APIRouter()
search_service = TrailerSearchService()

parent_dir = Path(__file__).resolve().parent.parent

CHROMA_DB_PATH = parent_dir / "chroma_db"

@router.post("/search", response_model=list[SearchResult])
async def search_scene(file: UploadFile = File(...), top_k: int = Form(3)):

    try:

        temp_dir = "client_uploads"

        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        raw_results = search_service.search(temp_file_path, top_k=top_k)

        return raw_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/update-chromadb")
def update_chromadb():
    try:
        #Backup old DB first
        backup_path = f"{dbManager.CHROMA_DB_PATH}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if dbManager.CHROMA_DB_PATH.exists():
            shutil.copytree(dbManager.CHROMA_DB_PATH, backup_path)
            print(f"🧾 Backup saved to {backup_path}")

        # Proceed with update
        dbManager.update_chromadb()

        return {"status": "success", "message": "ChromaDB updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))