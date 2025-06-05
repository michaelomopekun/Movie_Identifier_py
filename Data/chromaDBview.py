import chromadb
from pathlib import Path
# import numpy as np


parent_dir = Path(__file__).resolve().parent.parent

path_chromadb = parent_dir / "chromaDB"

def view_embeddings():

    chromaClient = chromadb.PersistentClient(str(path_chromadb))

    collection = chromaClient.get_or_create_collection(name="moviesTrailerEmbeddings")
    
    results = collection.get(
        include=["embeddings", "documents", "metadatas"]
    )
    
    # return results
    for i in range(len(results["ids"])):
        print(f"ID: {results['ids'][i]}")
        print(f"Document: {results['documents'][i]}")
        print(f"Metadata: {results['metadatas'][i]}")
        print(f"Embedding Vector (first 10 dims): {results['embeddings'][0].shape}")
        print("-" * 50)
    
    print(f"Total number of embeddings: {len(results['ids'])}")


if __name__ == "__main__":
    view_embeddings()
