import os
import cv2
import requests
import numpy as np
from PIL import Image
from pathlib import Path
import onnxruntime as ort
from dotenv import load_dotenv
from chromadb import PersistentClient
from transformers import CLIPProcessor
from models.response_model import SearchResult

load_dotenv()

onnxUrl = os.getenv("ONNX_MODEL_URL")
token = os.getenv("Hugging_Face_Authorization_Token")

parent_dir = Path(__file__).resolve().parent

path_onnx = parent_dir / "onnx" / "visual.onnx"

if not path_onnx.exists():
    response = requests.get(onnxUrl, headers={
        "User-Agent": "Mozilla/5.0",
        # "Authorization": token
    })
    path_onnx.parent.mkdir(parents=True, exist_ok=True)
    print("DownLoading visual.onnx model...")

    response.raise_for_status()
    with open(path_onnx, "wb") as f:
        f.write(response.content)

path_chromadb = parent_dir / "chromaDB"

class TrailerSearchService:

    def __init__(self, db_path=str(path_chromadb), model_path=str(path_onnx), num_frames = None):

        self.num_frames = int(num_frames or os.getenv("NUMBER_OF_FRAMES", 100))

        # Initialize onnx
        providers = ['DmlExecutionProvider']

        self.session = ort.InferenceSession(str(path_onnx))

        # Initialize clip
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

        # Initialize ChromaDB
        self.client = PersistentClient(path=db_path)

        self.collection = self.client.get_or_create_collection(name="moviesTrailerEmbeddings")


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

                # with open(path, "a", encoding="utf-8") as log_file:
                #     log_file.write(f"✅successfully read frame {frameId} from {videoPath}\n")

                print(f"✅successfully read frame {frameId} from {videoPath}")
            else:
                # with open(path, "a", encoding="utf-8") as log_file:
                #     log_file.write(f"❌Failed to read frame {frameId} from {videoPath}\n")

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
                
                # Log results
                # with open(path_result_log, "a", encoding="utf-8") as log_file:

                #     log_file.write(f"ID: {result.id}\n")
                #     log_file.write(f"Document: {result.document}\n")
                #     log_file.write(f"Metadata: {result.metadata}\n")
                #     log_file.write(f"Distance: {result.distance}\n")
                #     log_file.write("-" * 50 + "\n")

            return formatted_results
        
        except Exception as e:

            # with open(path_result_log, "a", encoding="utf-8") as log_file:
            #     log_file.write(f"❌Error: {str(e)}\n")
            raise e
