import os 
import requests
import numpy as np
from pathlib import Path
from os.path import basename
from models.response_model import SearchResult
from dotenv import load_dotenv
from chromadb import PersistentClient

load_dotenv()

embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL")

parent_dir = Path(__file__).resolve().parent.parent

path_chromadb = parent_dir / "chromaDB"

class TrailerSearchService:

    def __init__(self, db_path=str(path_chromadb),  num_frames = None):

        self.num_frames = int(num_frames or os.getenv("NUMBER_OF_FRAMES", 100))

        # Initialize ChromaDB
        self.client = PersistentClient(path=db_path)

        self.collection = self.client.get_or_create_collection(name="moviesTrailerEmbeddings")



    def embed_video_scene(self, video_path):

        with open(video_path, "rb") as vf:
            files = {"file": (basename(video_path), vf, "video/mp4")}
            response = requests.post(embedding_service_url, files=files)

        response.raise_for_status()

        embedding = response.json()["embedding"]

        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)

        elif isinstance(embedding, np.ndarray):
            embedding = embedding.astype(np.float32)

        else:
            raise ValueError("Unexpected type for embedding: {}".format(type(embedding)))
        
        if embedding is None:
            raise ValueError("Embedding not found in response")
        
        print(f"✅Successfully embedded video scene from {video_path}, embedding shape: {embedding.shape}")

        return embedding



    def search(self, video_path: str, top_k: int = 5):

        try:

            vector = self.embed_video_scene(video_path)

            results = self.collection.query(query_embeddings=[vector.tolist()], n_results=top_k)

            formatted_results = []
            for i in range(len(results["ids"][0])):

                result = SearchResult(
                    id=results["ids"][0][i],
                    document=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    distance=float(results["distances"][0][i])
                )
                formatted_results.append(result)

            return formatted_results
        
        except Exception as e:
            raise e