from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant


import os
import json

def initialize_embeddings():
    print("Initializing embedding model (baai/bge-m3)")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embedidngs": True}
    )
    return embeddings


def create_vector_store(documents, embeddings):
    persist_directory = "qdrant_db"
    os.makedirs(persist_directory, exist_ok=True)

    print(f"create qdrant vector store and persisting to {persist_directory}")
    vector_store = Qdrant.from_documents(
        documents=documents,
        embedding=embeddings,
        path=persist_directory,
        collection_name="places"
    )
    print(f"Vector store created and persisted successfullly")
    return vector_store


def load_existing_vector_store(embeddings):
    persist_directory = "../qdrant_db"
    if not os.path.exists(persist_directory):
        print(f"Error: directory {persist_directory} does not exist.")
        return None

    print(f"Loading existing Qdrant vector store from {persist_directory}")
    vector_store = Qdrant.from_documents(
        documents=[],
        persist_directory=persist_directory,
        embedding=embeddings,
        collection_name="places"
    )
    print("Vector store loaded successfully")
    return vector_store
