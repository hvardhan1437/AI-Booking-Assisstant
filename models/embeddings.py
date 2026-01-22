from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def build_vector_store(pdf_files):
    """
    Takes uploaded PDF files and returns a FAISS vector store
    """
    documents = []

    for pdf in pdf_files:
        loader = PyPDFLoader(pdf)
        documents.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


def retrieve_context(vector_store, query, k=3):
    """
    Retrieves top-k relevant chunks from FAISS
    """
    if not vector_store:
        return ""

    docs = vector_store.similarity_search(query, k=k)
    return "\n\n".join(doc.page_content for doc in docs)
