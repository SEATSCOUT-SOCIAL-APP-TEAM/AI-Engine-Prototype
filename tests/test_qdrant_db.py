from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os


from dotenv import load_dotenv
from llama_index.core.base.embeddings.base import similarity

from vector_search.qdrant_client import vectorstore

load_dotenv()

def setup_groq_llm():

    if 'GROQ_API_KEY' not in os.environ:
        if "GROQ_API_KEY" not in os.environ:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please set it before running this code.")

        print("Setting up Groq LLM...")

    llm = ChatGroq(api_key=os.environ['GROQ_API_KEY'],
                    model="llama3-8b-8192",
                   temperature=0.2,
                   max_tokens=1024)

    return llm


# Function to create a custom prompt template
def create_qa_prompt_template():
    template = """
You are a helpful assistant that helps users find information about places based on their preferences.
You have access to a vector database containing details about various places including restaurants, cafes, and other venues.

Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say you don't know. Don't try to make up an answer.

Context:
{context}

Question: {question}

Provide a detailed and helpful answer:
"""
    return PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )


def create_qa_chain(vector_store):
    llm = setup_groq_llm()
    prompt = create_qa_prompt_template()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}  # Retrieve top 3 most relevant documents
    )

    qa_chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm

    return qa_chain


# Function to answer user questions
def answer_question(qa_chain, question):
    print(f"\nQuestion: {question}")
    print("Thinking...")

    result = qa_chain.invoke({"query": question})

    print("\nAnswer:")
    print(result["result"])

    print("\nBased on:")
    for i, doc in enumerate(result["source_documents"]):
        print(f"Source {i + 1}: {doc.metadata.get('name', 'Unknown')}")
        print(f"Rating: {doc.metadata.get('rating', 'N/A')}")
        print(f"Tags: {doc.metadata.get('tags', 'N/A')}")
        print("-" * 40)

    return result


if __name__ == "__main__":
    vector_store = vectorstore
    qa_chain = create_qa_chain(vector_store)
    answer_question("find a cozy coffee shop for me?")
