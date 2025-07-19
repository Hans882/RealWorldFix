# clustering/embedder.py

from sentence_transformers import SentenceTransformer

# Load model only once at startup
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_descriptions(descriptions: list[str]) -> list[list[float]]:
    """
    Returns SBERT embeddings for a list of descriptions.
    """
    return sbert_model.encode(descriptions)
