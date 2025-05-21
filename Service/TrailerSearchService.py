import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import onnxruntime as ort
from models.response_model import SearchResult
from dotenv import load_dotenv
from chromadb import PersistentClient
from transformers import CLIPProcessor

load_dotenv()

parent_dir = Path(__file__).resolve().parent.parent

path_result_log = parent_dir / "logs" / "search_result_log.txt"
if not path_result_log.exists():
    path_result_log.touch()

path = parent_dir / "logs" / "processed_client_frame_log.txt"

path_onnx = parent_dir / "onnx" / "visual.onnx"

path_chromadb = parent_dir / "chromaDB"

class TrailerSearchService:

    def __init__(self, db_path=str(path_chromadb), model_path=str(path_onnx), num_frames = None):

        self.num_frames = int(num_frames or os.getenv("NUMBER_OF_FRAMES", 100))

        # Initialize onnx
        providers = ['DmlExecutionProvider']

        self.session = ort.InferenceSession(model_path, providers=providers)

        # Initialize clip
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

        # Initialize ChromaDB
        self.client = PersistentClient(path=db_path)

        self.collection = self.client.get_collection(name="moviesTrailerEmbeddings")


    def extract_frames(self, videoPath):

        cap = cv2.VideoCapture(videoPath)
        totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if totalFrames < self.num_frames:
            frameIds = list(range(totalFrames))
        else:
            step = max(totalFrames // self.num_frames, 1)
            frameIds = [i * step for i in range(self.num_frames)]


        frames = []

        for frameId in frameIds:

            cap.set(cv2.CAP_PROP_POS_FRAMES, frameId)

            success, frame = cap.read()

            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                frames.append(Image.fromarray(frame))

                with open(path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"✅successfully read frame {frameId} from {videoPath}\n")

                print(f"✅successfully read frame {frameId} from {videoPath}")
            else:
                with open(path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"❌Failed to read frame {frameId} from {videoPath}\n")

                print(f"❌Failed to read frame {frameId} from {videoPath}")
                continue

        cap.release()

        return frames



    def embed_video_scene(self, video_path):

        frames = self.extract_frames(video_path)
        if not frames:
            raise ValueError(f"No frames extracted from video: {video_path}")

        inputs = self.processor(images=frames, return_tensors="pt", padding=True)["pixel_values"].numpy()

        outputs = self.session.run(None, {"input": inputs})

        embedding = outputs[0]

        embedding /= np.linalg.norm(embedding, axis=-1, keepdims=True)
        
        embedding = embedding.mean(axis=0)

        return embedding



    def search(self, video_path: str, top_k: int = 5):

        vector = self.embed_video_scene(video_path)

        results = self.collection.query(query_embeddings=[vector.tolist()], n_results=top_k)

        formatted_results = [
            SearchResult(
                id=id_,
                document=document,
                metadata=metadata,
                distance=distance
            )
            for id_, document, metadata, distance in zip(
                results["ids"],
                results["documents"],
                results["metadatas"],
                results["distances"]
            )
        ]

        return formatted_results
