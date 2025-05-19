import cv2
import numpy as np
from PIL import Image
from chromadb import PersistentClient
from transformers import CLIPProcessor
import onnxruntime as ort
import os
from dotenv import load_dotenv

load_dotenv()

class TrailerSearchService:

    def __init__(self, db_path="./chromaDB", model_path="visual.onnx", num_frames = None):

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

                with open("logs/processed_client_frame_log.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"✅successfully read frame {frameId} from {videoPath}\n")

                print(f"✅successfully read frame {frameId} from {videoPath}")
            else:
                with open("logs/processed_client_frame_log.txt", "a", encoding="utf-8") as log_file:
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

        return [
            {
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
                "distance": results["distances"][i]
            }
            for i in range(len(results["ids"]))
        ]
