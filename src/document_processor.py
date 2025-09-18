import os
import hashlib
from typing import List, Dict, Optional
from langchain.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
import numpy as np
from sentence_transformers import SentenceTransformer

class AdaptiveDocumentProcessor:
    def __init__(self):
        # Multiple text splitters for different content types
        self.code_splitter = RecursiveCharacterTextSplitter(
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
            chunk_size=800,  # Smaller for code
            chunk_overlap=100,
            length_function=len
        )
        
        self.doc_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""],
            chunk_size=1200,  # Larger for documentation
            chunk_overlap=200,
            length_function=len
        )
        
        # Semantic chunking splitter
        self.semantic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Even larger for semantic coherence
            chunk_overlap=300,
            length_function=len
        )
        
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        # Cache for document hashes to avoid reprocessing
        self.doc_cache = {}
        
    def get_document_hash(self, doc: Document) -> str:
        """Generate hash for document content to detect duplicates"""
        content = doc.page_content + str(doc.metadata)
        return hashlib.md5(content.encode()).hexdigest()
    
    def classify_document_type(self, doc: Document) -> str:
        """Classify document type for optimal chunking strategy"""
        content = doc.page_content.lower()
        metadata = doc.metadata
        
        # Check file extension first
        source = metadata.get('source', '').lower()
        if any(ext in source for ext in ['.py', '.js', '.java', '.cpp']):
            return 'code'
        
        # Check content patterns
        code_patterns = ['def ', 'class ', 'function', 'import ', 'from ', '#!/']
        if any(pattern in content for pattern in code_patterns):
            return 'code'
        
        # Check for API documentation patterns
        api_patterns = ['endpoint', 'parameter', 'response', 'request', 'api']
        if any(pattern in content for pattern in api_patterns):
            return 'api'
        
        return 'documentation'
    
    def adaptive_chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Adaptively chunk documents based on content type"""
        processed_docs = []
        doc_type_stats = {'code': 0, 'api': 0, 'documentation': 0}
        
        for doc in documents:
            # Skip if already processed (cache check)
            doc_hash = self.get_document_hash(doc)
            if doc_hash in self.doc_cache:
                processed_docs.extend(self.doc_cache[doc_hash])
                continue
            
            # Classify and chunk accordingly
            doc_type = self.classify_document_type(doc)
            doc_type_stats[doc_type] += 1
            
            if doc_type == 'code':
                chunks = self.code_splitter.split_documents([doc])
            elif doc_type == 'api':
                # API docs benefit from semantic chunking
                chunks = self.semantic_splitter.split_documents([doc])
            else:
                chunks = self.doc_splitter.split_documents([doc])
            
            # Add document type to metadata
            for chunk in chunks:
                chunk.metadata['doc_type'] = doc_type
                chunk.metadata['chunk_id'] = f"{doc_hash}_{len(processed_docs)}"
            
            # Cache the processed chunks
            self.doc_cache[doc_hash] = chunks
            processed_docs.extend(chunks)
        
        print(f"📊 Document type distribution: {doc_type_stats}")
        return processed_docs
    
    def filter_quality_chunks(self, documents: List[Document], 
                            min_length: int = 100,
                            max_length: int = 3000) -> List[Document]:
        """Enhanced quality filtering with content analysis"""
        quality_docs = []
        
        for doc in documents:
            content = doc.page_content.strip()
            
            # Basic length filtering
            if len(content) < min_length or len(content) > max_length:
                continue
            
            # Skip chunks that are mostly whitespace or repeated characters
            if len(content.replace(' ', '').replace('\n', '')) < min_length * 0.7:
                continue
                
            # Skip chunks with too many repeated lines (likely formatting artifacts)
            lines = content.split('\n')
            unique_lines = set(lines)
            if len(lines) > 10 and len(unique_lines) / len(lines) < 0.5:
                continue
            
            # Calculate content entropy (diversity measure)
            char_counts = {}
            for char in content.lower():
                if char.isalnum():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                total_chars = sum(char_counts.values())
                entropy = -sum((count/total_chars) * np.log2(count/total_chars) 
                              for count in char_counts.values())
                
                # Skip chunks with very low entropy (repetitive content)
                if entropy < 2.0:
                    continue
            
            quality_docs.append(doc)
        
        print(f"📈 Quality filtering: {len(documents)} → {len(quality_docs)} chunks")
        return quality_docs

    def create_optimized_vector_store(self, documents: List[Document], 
                                    persist_directory: str = "./data/chroma_db") -> Chroma:
        """Create vector store with optimized settings"""
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Create vector store with optimized collection settings
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=persist_directory,
            collection_metadata={
                "hnsw:space": "cosine",  # Better for normalized embeddings
                "hnsw:construction_ef": 200,  # Higher for better quality
                "hnsw:M": 16,  # Good balance of speed/accuracy
                "hnsw:ef_search": 100,  # Search time quality
            }
        )
        
        return vector_store
    
    def batch_process_embeddings(self, texts: List[str], batch_size: int = 50):
        """Optimized batch embedding generation"""
        embeddings = []
        
        # Use sentence-transformers directly for better batching
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = model.encode(
                batch,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=batch_size,
                show_progress_bar=False
            )
            embeddings.extend(batch_embeddings.tolist())
            
        return embeddings

    def process_documents_pipeline(self, folder_path: str) -> Chroma:
        """Complete optimized document processing pipeline"""
        print("🚀 Starting optimized document processing...")
        
        # 1. Load documents
        documents = self.load_documents(folder_path)
        if not documents:
            raise ValueError("No documents found!")
        
        # 2. Adaptive chunking
        chunks = self.adaptive_chunk_documents(documents)
        
        # 3. Quality filtering
        quality_chunks = self.filter_quality_chunks(chunks)
        
        # 4. Create optimized vector store
        vector_store = self.create_optimized_vector_store(quality_chunks)
        
        print(f"✅ Processing complete: {len(quality_chunks)} high-quality chunks")
        return vector_store
    
    def load_documents(self, folder_path: str) -> List[Document]:
        """Load documents with better error handling"""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Documents folder not found: {folder_path}")
        
        documents = []
        loaders = [
            (DirectoryLoader(folder_path, glob="**/*.txt", loader_cls=TextLoader), "text"),
            (DirectoryLoader(folder_path, glob="**/*.pdf", loader_cls=PyPDFLoader), "pdf"),
        ]
        
        for loader, file_type in loaders:
            try:
                docs = loader.load()
                documents.extend(docs)
                print(f"📄 Loaded {len(docs)} {file_type} files")
            except Exception as e:
                print(f"⚠️ Warning loading {file_type} files: {e}")
        
        return documents
