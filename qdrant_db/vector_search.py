from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

import os


class VectorSearch:
    def __init__(self, collection_name: str = 'places'):
        # Initialize the embedding model
        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name='baai/bge-m3',
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize Qdrant client
        self.qdrant = self.load_existing_vector_store(self.embedding_model)
        self.collection_name = collection_name

    # Step 9: Function to load from existing Qdrant DB
    def load_existing_vector_store(self, embeddings):
        persist_directory = "qdrant_db"
        if not os.path.exists(persist_directory):
            print(f"Error: Directory {persist_directory} does not exist.")
            return None

        print(f"Loading existing Qdrant vector store from {persist_directory}")
        client = QdrantClient(path=persist_directory)
        vector_store = Qdrant(client=client, collection_name="places", embeddings=embeddings)
        print("Vector store loaded successfully")
        return vector_store

    def encode_query(self, query: str) -> List[float]:
        """Encode the query text into vector embeddings."""
        return self.embedding_model.embed_query(query)

    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic similarity search on the vector database.

        Args:
            query: User's search query
            limit: Maximum number of results to return

        Returns:
            List of dictionaries containing search results with scores
        """
        # Encode the query
        query_vector = self.encode_query(query)

        # Search in Qdrant
        search_results = self.qdrant.similarity_search(
            query
        )

        # Format results
        results = []
        for res in search_results:
            result = {
                'id': res.metadata['id'],
                'content': res.page_content,
                'payload': res.metadata
            }
            results.append(result)

        return results

    def get_place_by_id(self, place_id: str) -> Dict[str, Any]:
        """Retrieve a specific place by its ID."""
        points = self.qdrant.retrieve(
            collection_name=self.collection_name,
            ids=[place_id]
        )
        return points[0].payload if points else None
