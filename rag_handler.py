__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
#--------------------------------------------------------------------------#
# OPSI A (Lama/Legacy)
#from langchain.text_splitter import RecursiveCharacterTextSplitter
# OPSI B (Baru/Modular - Direkomendasikan) - (v0.1+)
from langchain_text_splitters import RecursiveCharacterTextSplitter
#--------------------------------------------------------------------------#
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

# Initialize ChromaDB client persistent storage
CHROMA_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection_name = "mermaid_rag"

# Use local HuggingFace embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Get or create collection
collection = chroma_client.get_or_create_collection(name=collection_name)

def process_and_add_document(file_path: str, document_id: int):
    """
    Processes a PDF or TXT file, splits it into chunks, and adds it to ChromaDB.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # Load document
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
    elif ext == '.txt':
        loader = TextLoader(file_path, encoding='utf-8')
    else:
        raise ValueError("Unsupported file format")

    documents = loader.load()

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Prepare data for Chroma
    texts = [doc.page_content for doc in docs]
    metadatas = [{"document_id": document_id, "source": file_path} for _ in docs]
    ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(docs))]

    # Embed and store
    embeds = embeddings.embed_documents(texts)
    collection.add(
        documents=texts,
        embeddings=embeds,
        metadatas=metadatas,
        ids=ids
    )

def delete_document_vectors(document_id: int):
    """
    Deletes all vector chunks associated with a document_id.
    """
    collection.delete(where={"document_id": document_id})

def query_rag_context(query: str, selected_document_ids: list[int] = None, n_results=3):
    """
    Queries ChromaDB for relevant context based on selected document IDs.
    """
    if not selected_document_ids:
        return ""

    query_embedding = embeddings.embed_query(query)
    
    # Filter by selected document IDs
    # Chroma 'in' operator syntax for metadata filtering
    filter_dict = {"document_id": {"$in": selected_document_ids}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=filter_dict
    )

    if not results['documents'] or not results['documents'][0]:
        return ""

    # Combine the top results into a single context string
    context = "\n\n".join(results['documents'][0])
    return context
