import json
from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
import os


# Step 1: Create a sample JSON file with the provided schema

# Step 2: Define the metadata extraction function for JSONLoader
def metadata_func(record, metadata):
    # Extract all fields as metadata
    metadata["id"] = record.get("id", "")
    metadata["name"] = record.get("name", "")
    metadata["tags"] = ", ".join(record.get("tags", []))
    metadata["ambience"] = ", ".join(record.get("ambience", []))
    metadata["popularity"] = record.get("popularity", "")
    metadata["rating"] = record.get("rating", 0)
    metadata["review_sentiment"] = record.get("review_sentiment", "")
    metadata["opening_hours"] = " - ".join(record.get("opening_hours", []))
    metadata["location"] = f"{record.get('lat', 0)}, {record.get('lon', 0)}"
    metadata["busy_hours"] = ", ".join(str(hour) for hour in record.get("busy_hours", []))

    # We'll include reviews in the content, but add a reference to them in metadata
    metadata["has_reviews"] = len(record.get("reviews", [])) > 0
    metadata["review_count"] = len(record.get("reviews", []))

    return metadata


# Step 3: Define content extraction for the JSONLoader
def content_func(record):
    # Combine the name, description, and reviews into the content
    content_parts = [record.get("name", ""), record.get("description", "")]

    # Add reviews to the content
    reviews = record.get("reviews", [])
    if reviews:
        content_parts.append("Reviews:")
        for review in reviews:
            content_parts.append(f"- {review}")

    return "\n\n".join(content_parts)


# Step 4: Load the JSON data
def load_json_data(json_path):
    print(f"Loading data from {json_path}")
    loader = JSONLoader(
        file_path=json_path,
        jq_schema='.[]',
        content_key=None,  # We'll use a custom content extractor instead
        content_extractor=content_func,
        metadata_func=metadata_func
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")
    return documents


# Step 5: Split documents if needed
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)
    print(f"Split into {len(splits)} chunks")
    return splits


# Step 6: Initialize HuggingFace embeddings with the specified model
def initialize_embeddings():
    print("Initializing embedding model (baai/bge-m3)")
    embeddings = HuggingFaceEmbeddings(
        model_name="baai/bge-m3",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return embeddings


# Step 7: Create and persist Qdrant vector store
def create_vector_store(documents, embeddings):
    # Create a directory for persistence if it doesn't exist
    persist_directory = "qdrant_db"
    os.makedirs(persist_directory, exist_ok=True)

    print(f"Creating Qdrant vector store and persisting to {persist_directory}")
    vector_store = Qdrant.from_documents(
        documents=documents,
        embedding=embeddings,
        path=persist_directory,  # Local persistence
        collection_name="places"
    )
    print(f"Vector store created and persisted successfully")
    return vector_store


# Step 8: Test queries to verify everything works
def test_queries(vector_store):
    print("\nTesting queries...")

    # Test various queries to demonstrate search capabilities
    queries = [
        "Where can I find vegan food?",
        "I'm looking for a cozy place with good reviews",
        "Recommend a popular restaurant"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.similarity_search(query, k=1)

        for i, doc in enumerate(results):
            print(f"Result {i + 1}: {doc.metadata.get('name', 'Unknown')}")
            print(f"Content: {doc.page_content[:100]}...")  # Show first 100 chars
            print(f"Tags: {doc.metadata.get('tags', '')}")
            print(f"Rating: {doc.metadata.get('rating', '')}")
            print(f"Popularity: {doc.metadata.get('popularity', '')}")


# Step 9: Function to load from existing Qdrant DB
def load_existing_vector_store(embeddings):
    persist_directory = "qdrant_db"
    if not os.path.exists(persist_directory):
        print(f"Error: Directory {persist_directory} does not exist.")
        return None

    print(f"Loading existing Qdrant vector store from {persist_directory}")
    vector_store = Qdrant.load(
        path=persist_directory,
        embedding_function=embeddings,
        collection_name="places"
    )
    print("Vector store loaded successfully")
    return vector_store


# Main execution
def main():
    # Create or use existing JSON file
    json_path = "../realistic_places_with_location.json"  # Replace with your JSON path if you have one

    # Process pipeline
    documents = load_json_data(json_path)
    splits = split_documents(documents)
    embeddings = initialize_embeddings()
    vector_store = create_vector_store(splits, embeddings)
    test_queries(vector_store)

    # Example of loading the persisted database
    print("\nDemonstrating how to load the persisted database:")
    loaded_vector_store = load_existing_vector_store(embeddings)
    if loaded_vector_store:
        print("Successfully loaded the persisted vector store")


if __name__ == "__main__":
    main()