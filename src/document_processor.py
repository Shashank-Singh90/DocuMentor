import os
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document

class DocumentProcessor:
    def __init__(self, ollama_base_url: str = "http://localhost:11435"):
        self.embeddings = OllamaEmbeddings(
            base_url=ollama_base_url,
            model="nomic-embed-text"
        )
        # Optimized chunking for quality + efficiency
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,        # Good context size
            chunk_overlap=100,     # Sufficient overlap
            separators=["\n\n", "\n", ". ", " "]  # Smart splitting
        )
        self.vector_store = None
    
    def load_documents(self, folder_path: str) -> List[Document]:
        """Load documents with quality filtering"""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Documents folder not found: {folder_path}")
        
        documents = []
        
        try:
            # Load text files
            txt_loader = DirectoryLoader(
                folder_path,
                glob="**/*.txt",
                loader_cls=TextLoader
            )
            txt_docs = txt_loader.load()
            documents.extend(txt_docs)
            
            # Load PDF files
            pdf_loader = DirectoryLoader(
                folder_path, 
                glob="**/*.pdf", 
                loader_cls=PyPDFLoader
            )
            pdf_docs = pdf_loader.load()
            documents.extend(pdf_docs)
            
            print(f"Loaded {len(documents)} documents")
            
        except Exception as e:
            print(f"Warning: Could not load some documents: {e}")
        
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process documents with quality filtering"""
        if not documents:
            raise ValueError("No documents to process")
        
        processed_docs = self.text_splitter.split_documents(documents)
        
        # Filter out very short or empty chunks
        quality_docs = [
            doc for doc in processed_docs 
            if len(doc.page_content.strip()) > 50  # Minimum content length
        ]
        
        print(f"Created {len(quality_docs)} quality document chunks")
        return quality_docs
    
    def create_vector_store(self, documents: List[Document], persist_directory: str = "./data/chroma_db"):
        """Create optimized vector store"""
        if not documents:
            raise ValueError("No documents to create vector store from")
            
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=persist_directory,
        )
        return self.vector_store
    
    def load_vector_store(self, persist_directory: str = "./data/chroma_db"):
        """Load existing vector store"""
        if not os.path.exists(persist_directory):
            raise FileNotFoundError(f"Vector store not found at {persist_directory}")
            
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        return self.vector_store
    
    def search_documents(self, query: str, k: int = 3):
        """Search with optimal retrieval settings"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.similarity_search(query, k=k)
