import time
from typing import List, Dict, Tuple, Optional
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
import numpy as np
from sentence_transformers import CrossEncoder
from collections import defaultdict
import re

class OptimizedRetriever:
    def __init__(self, vector_store: Chroma, llm):
        self.vector_store = vector_store
        self.llm = llm
        
        # Initialize cross-encoder for reranking
        try:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            self.use_reranking = True
        except:
            print("⚠️ Reranker not available, using similarity only")
            self.use_reranking = False
        
        # Query expansion keywords
        self.expansion_keywords = {
            'error': ['exception', 'bug', 'issue', 'problem', 'fail'],
            'install': ['setup', 'configure', 'deploy', 'initialize'],
            'example': ['tutorial', 'guide', 'demo', 'sample'],
            'api': ['endpoint', 'method', 'function', 'call'],
            'performance': ['optimization', 'speed', 'fast', 'efficient'],
        }
        
        # Response cache
        self.cache = {}
        self.cache_max_size = 100
        
    def expand_query(self, query: str) -> str:
        """Intelligently expand query with related terms"""
        expanded_terms = []
        query_lower = query.lower()
        
        for key, synonyms in self.expansion_keywords.items():
            if key in query_lower:
                # Add most relevant synonym
                for synonym in synonyms:
                    if synonym not in query_lower:
                        expanded_terms.append(synonym)
                        break
        
        if expanded_terms:
            expanded_query = f"{query} {' '.join(expanded_terms[:2])}"
            print(f"🔍 Expanded query: '{query}' → '{expanded_query}'")
            return expanded_query
        
        return query
    
    def calculate_dynamic_k(self, query: str, max_k: int = 10) -> int:
        """Dynamically calculate optimal number of documents to retrieve"""
        query_length = len(query.split())
        
        # More specific queries need fewer documents
        if query_length >= 10:
            return min(3, max_k)
        elif query_length >= 6:
            return min(5, max_k)
        else:
            return min(8, max_k)  # Broad queries benefit from more context
    
    def retrieve_with_fallback(self, query: str, k: int) -> List[Document]:
        """Retrieve documents with multiple fallback strategies"""
        
        # Strategy 1: MMR retrieval (current method)
        try:
            docs = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": k,
                    "lambda_mult": 0.7,
                    "fetch_k": k * 2  # Fetch more, then diversify
                }
            ).get_relevant_documents(query)
            
            if docs:
                return docs
                
        except Exception as e:
            print(f"⚠️ MMR retrieval failed: {e}")
        
        # Strategy 2: Similarity search with threshold
        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query, k=k
            )
            
            # Filter by similarity threshold
            threshold = 0.7
            filtered_docs = [
                doc for doc, score in docs_with_scores 
                if score > threshold
            ]
            
            if filtered_docs:
                return filtered_docs[:k]
                
        except Exception as e:
            print(f"⚠️ Similarity search failed: {e}")
        
        # Strategy 3: Basic similarity search (fallback)
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"❌ All retrieval methods failed: {e}")
            return []
    
    def rerank_documents(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents using cross-encoder"""
        if not self.use_reranking or len(documents) <= 1:
            return documents
        
        try:
            # Prepare query-document pairs
            pairs = [(query, doc.page_content) for doc in documents]
            
            # Get reranking scores
            scores = self.reranker.predict(pairs)
            
            # Sort documents by reranking scores
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            reranked_docs = [doc for doc, score in doc_score_pairs]
            
            print(f"🎯 Reranked {len(documents)} documents")
            return reranked_docs
            
        except Exception as e:
            print(f"⚠️ Reranking failed: {e}")
            return documents
    
    def filter_by_document_type(self, query: str, documents: List[Document]) -> List[Document]:
        """Filter documents based on query intent"""
        query_lower = query.lower()
        
        # Detect query intent
        if any(word in query_lower for word in ['example', 'tutorial', 'how to', 'guide']):
            # Prefer documentation and examples
            preferred_types = ['documentation', 'api']
        elif any(word in query_lower for word in ['function', 'method', 'class', 'code']):
            # Prefer code examples
            preferred_types = ['code', 'api']
        else:
            # No filtering
            return documents
        
        # Filter documents by preferred types
        filtered = []
        remaining = []
        
        for doc in documents:
            doc_type = doc.metadata.get('doc_type', 'documentation')
            if doc_type in preferred_types:
                filtered.append(doc)
            else:
                remaining.append(doc)
        
        # Return filtered first, then remaining
        result = filtered + remaining
        
        if len(filtered) > 0:
            print(f"📋 Prioritized {len(filtered)} documents by type")
        
        return result
    
    def get_cache_key(self, query: str, k: int) -> str:
        """Generate cache key for query"""
        return f"{hash(query)}_{k}"
    
    def retrieve_documents(self, query: str, use_expansion: bool = True) -> List[Document]:
        """Main retrieval method with all optimizations"""
        start_time = time.time()
        
        # Check cache first
        k = self.calculate_dynamic_k(query)
        cache_key = self.get_cache_key(query, k)
        
        if cache_key in self.cache:
            print(f"⚡ Cache hit for query: '{query[:50]}...'")
            return self.cache[cache_key]
        
        # Expand query if enabled
        if use_expansion:
            expanded_query = self.expand_query(query)
        else:
            expanded_query = query
        
        # Retrieve documents with fallback
        documents = self.retrieve_with_fallback(expanded_query, k)
        
        if not documents:
            print("❌ No documents retrieved")
            return []
        
        # Filter by document type based on query intent
        documents = self.filter_by_document_type(query, documents)
        
        # Rerank documents
        if len(documents) > 1:
            documents = self.rerank_documents(query, documents)
        
        # Cache the result
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[cache_key] = documents
        
        retrieval_time = time.time() - start_time
        print(f"🔍 Retrieved {len(documents)} documents in {retrieval_time:.2f}s")
        
        return documents
    
    def create_optimized_qa_chain(self, custom_prompt: Optional[str] = None):
        """Create optimized QA chain with custom retriever"""
        
        class OptimizedRetrieverWrapper:
            def __init__(self, retriever_instance):
                self.retriever = retriever_instance
            
            def get_relevant_documents(self, query: str) -> List[Document]:
                return self.retriever.retrieve_documents(query)
        
        retriever_wrapper = OptimizedRetrieverWrapper(self)
        
        # Custom prompt for better responses
        if not custom_prompt:
            custom_prompt = """Use the following pieces of context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Focus on providing:
            1. Direct answers to the question
            2. Relevant code examples if available
            3. Step-by-step instructions when applicable
            
            Context:
            {context}
            
            Question: {question}
            Helpful Answer:"""
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever_wrapper,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": custom_prompt
            }
        )
        
        return qa_chain
    
    def ask_with_confidence(self, question: str, confidence_threshold: float = 0.3) -> Dict:
        """Ask question with confidence scoring"""
        start_time = time.time()
        
        # Get documents
        docs = self.retrieve_documents(question)
        
        if not docs:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "confidence": 0.0,
                "sources": [],
                "response_time": time.time() - start_time
            }
        
        # Calculate confidence based on document relevance
        confidence = min(1.0, len(docs) / 5.0)  # Simple confidence metric
        
        # Create QA chain and get answer
        qa_chain = self.create_optimized_qa_chain()
        
        try:
            result = qa_chain({"query": question})
            
            response = {
                "answer": result["result"],
                "confidence": confidence,
                "sources": result.get("source_documents", docs),
                "response_time": time.time() - start_time,
                "num_docs_used": len(docs)
            }
            
            # Add low confidence warning
            if confidence < confidence_threshold:
                response["warning"] = "Low confidence answer - information may be incomplete"
            
            return response
            
        except Exception as e:
            print(f"❌ QA chain failed: {e}")
            return {
                "answer": f"Error processing your question: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "response_time": time.time() - start_time
            }
    
    def get_retrieval_stats(self) -> Dict:
        """Get retrieval performance statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_hit_ratio": getattr(self, '_cache_hits', 0) / max(getattr(self, '_total_queries', 1), 1),
            "reranking_enabled": self.use_reranking,
            "avg_retrieval_time": getattr(self, '_avg_retrieval_time', 0),
        }
        