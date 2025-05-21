from fastapi import APIRouter, UploadFile, File, HTTPException
from Service.TrailerSearchService import TrailerSearchService
from models.response_model import SearchResult
from pathlib import Path
import shutil
import os

router = APIRouter()
search_service = TrailerSearchService()

parent_dir = Path(__file__).resolve().parent.parent

path_result_log = parent_dir / "logs" / "search_result_log.txt"
if not path_result_log.exists():
    path_result_log.touch()


@router.post("/search", response_model=list[SearchResult])
async def search_scene(file: UploadFile = File(...), top_k: int = 3):

    try:

        temp_dir = "client_uploads"

        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        results = search_service.search(temp_file_path, top_k=top_k)

        for match in results:

            with open(path_result_log, "a", encoding="utf-8") as log_file:
                log_file.write(f"ID: {match['id']}\n")
                log_file.write(f"Document: {match['document']}\n")
                log_file.write(f"Metadata: {match['metadata']}\n")
                log_file.write(f"Distance: {match['distance']}\n")
                log_file.write("-" * 50 + "\n")

        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)