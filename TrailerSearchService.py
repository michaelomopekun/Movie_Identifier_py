import numpy as np
from PIL import Image
from chromadb import PersistentClient
from transformers import CLIPProcessor
import onnxruntime as ort




class TrailerSearchService:

    def __init__(self, db_path="./chromaDB", model_path="visual.onnx"):

        # Initialize onnx
        providers = ['DmlExecutionProvider']

        self.session = ort.InferenceSession(model_path, providers=providers)

        # Initialize clip
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

        # Initialize ChromaDB
        self.client = PersistentClient(path=db_path)

        self.collection = self.client.get_collection(name="moviesTrailerEmbeddings")



    def embed_image(self, image_path: str) -> np.ndarray:

        image = Image.open(image_path).convert("RGB")

        inputs = self.processor(images=[image], return_tensors="pt", padding=True)["pixel_values"].numpy()

        outputs = self.session.run(None, {"input": inputs})

        embedding = outputs[0][0]

        embedding /= np.linalg.norm(embedding)

        return embedding



    def search(self, image_path: str, top_k: int = 5):

        query_vector = self.embed_image(image_path)

        results = self.collection.query(query_embeddings=[query_vector.tolist()], n_results=top_k)

        return [
            {
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i]
            }
            for i in range(len(results["ids"]))
        ]
