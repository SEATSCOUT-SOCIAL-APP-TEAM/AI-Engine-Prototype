# vector_search/vector_db.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from typing import List, Dict
from dataclasses import dataclass
import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings

@dataclass
class Location:
    id: str
    name: str
    latitude: float
    longitude: float
    category: str
    description: str
    metadata: Dict


class VectorSearchEngine:
    def __init__(self, connection_params: dict):
        """Initialize qdrant client and embedding model"""
        persist_path = "../qdrant_db"
        self.qdrant_client = QdrantClient(path=persist_path)
        self.embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        self._check_collection()

    def _check_collection(self):
        """check if the locations collection exists and is accessible"""
        try:
            collection_info = self.qdrant_client.get_collections(collection_name="places")
        except Exception as e:
            raise Exception("Failed to access the existing vector database")

    def index_location(self, location: Location):
        """Index a location with its vector representation"""
        vector = self._get_location_embedding(location.description)
        point = PointStruct(
            id=location.id,
            vector=vector,
            payload={
                "name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "category": location.category,
                "description": location.description,
                "metadata": location.metadata
            }
        )
        self.qdrant_client.upsert(
            collection_name="places",
            points=[point]
        )


    def search_similar(self, query_text: str, limit: int = 10) -> List[Location]:
        """search for similar locations using query text"""
        query_vector = self._get_location_embedding(query_text)

        results = self.qdrant_client.search(
            collection_name="places",
            query_vector=query_vector,
            limit=limit
        )
        locations = []
        for hit in results:
            payload = hit.payload
            location = Location(
                id=str(hit.id),
                name=payload["name"],
                latitude=payload["latitude"],
                longitude=payload["longitude"],
                category=payload["category"],
                description=payload["description"],
                metadata=payload["metadata"]
            )
            locations.append(location)

        return locations


    def update_index(self, location_id: str, vector: np.ndarray):
        """Update the vector representation of an existing location."""
        self.qdrant_client.update_vectors(
            collection_name="locations",
            points=[(location_id, vector)]
        )

    def _get_location_embedding(self, text: str) -> List[float]:
        """Get vector embedding for location text using baai/bge-m3 model."""
        embedding = self.embedding_model.embed_query(text)
        return embedding
