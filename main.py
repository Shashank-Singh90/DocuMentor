import os
import time
from dotenv import load_dotenv
from src.llm_handler import OptimizedLLMHandler
from src.document_processor import DocumentProcessor
from src.optimized_retriever import OptimizedRetriever
from src.optimized_chromadb import OptimizedChromaVectorStore
from src.optimized_retriever import OptimizedRetriever
from src.optimized_chromadb import OptimizedChromaVectorStore
from src.advanced_config import ConfigManager

load_dotenv()

class OptimizedDocuApp:
    def __init__(self):
        print("🚀 Initializing Optimized Docu RAG System...")
        
        # Initialize optimized components
        self.llm_handler = OptimizedLLMHandler()
        self.doc_processor = DocumentProcessor()
        self.vector_store = OptimizedChromaVectorStore()
        self.retriever = None
        
        # Performance tracking
        self.startup_time = time.time()
        
    def setup_optimized_rag_system(self, documents_folder: str = "./data/documents"):
        """Set up optimized RAG system with all performance enhancements"""
        print(f"📚 Setting up optimized RAG system from: {documents_folder}")
        start_time = time.time()
        
        try:
            # Check if vector store already has documents
            stats = self.vector_store.get_collection_stats()
            if stats['total_chunks'] > 0:
                print(f"✅ Found existing vector store with {stats['total_chunks']} documents")
                
                # Create retriever with existing vector store
                self.retriever = OptimizedRetriever(self.vector_store, self.llm_handler.llm)
                
                # Warm up the system
                self._warm_up_system()
                
                setup_time = time.time() - start_time
                print(f"🎉 Optimized RAG system ready in {setup_time:.2f}s!")
                return True
            
            # Process new documents
            print("📄 Processing documents with adaptive chunking...")
            documents = self.doc_processor.load_documents(documents_folder)
            
            if not documents:
                print("❌ No documents found!")
                return False
            
            # Adaptive processing pipeline
            chunks = self.doc_processor.adaptive_chunk_documents(documents)
            quality_chunks = self.doc_processor.filter_quality_chunks(chunks)
            
            if not quality_chunks:
                print("❌ No quality chunks generated!")
                return False
            
            # Add to optimized vector store
            print("🗄️  Adding documents to optimized vector store...")
            texts = [chunk.page_content for chunk in quality_chunks]
            metadatas = [chunk.metadata for chunk in quality_chunks]
            ids = [f"doc_{i}_{hash(text)}" for i, text in enumerate(texts)]
            
            success = self.vector_store.add_documents_optimized(texts, metadatas, ids)
            
            if not success:
                print("⚠️  Some documents failed to add, but system is functional")
            
            # Create optimized retriever
            self.retriever = OptimizedRetriever(self.vector_store, self.llm_handler.llm)
            
            # Warm up the system
            self._warm_up_system()
            
            setup_time = time.time() - start_time
            print(f"🎉 Optimized RAG system setup complete in {setup_time:.2f}s!")
            return True
            
        except Exception as e:
            print(f"❌ RAG system setup failed: {e}")
            return False
    
    def _warm_up_system(self):
        """Warm up all system components"""
        print("🔥 Warming up system components...")
        
        # Warm up LLM
        self.llm_handler.warm_up_model()
        
        # Warm up retriever with a test query
        if self.retriever:
            try:
                test_docs = self.retriever.retrieve_documents("test query", use_expansion=False)
                print(f"✅ Retriever warmed up - found {len(test_docs)} test documents")
            except Exception as e:
                print(f"⚠️  Retriever warm-up warning: {e}")
    
    def ask_question_optimized(self, question: str, confidence_threshold: float = 0.3):
        """Ask question with all optimizations enabled"""
        if not self.retriever:
            return {
                "answer": "Please set up the RAG system first.",
                "confidence": 0.0,
                "sources": [],
                "response_time": 0
            }
        
        try:
            print(f"🔍 Processing question: {question[:50]}...")
            result = self.retriever.ask_with_confidence(question, confidence_threshold)
            
            # Add system performance info
            result["system_stats"] = {
                "llm_stats": self.llm_handler.get_performance_stats(),
                "retrieval_stats": self.retriever.get_retrieval_stats(),
                "vector_store_stats": self.vector_store.get_collection_stats()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Question processing failed: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "response_time": 0
            }
    
    def simple_chat_optimized(self, message: str):
        """Simple chat with LLM optimizations"""
        return self.llm_handler.generate_response_optimized(message)
    
    def get_system_health(self):
        """Get comprehensive system health status"""
        health = {
            "llm_connection": False,
            "vector_store_healthy": False,
            "retriever_ready": False,
            "total_documents": 0,
            "system_uptime": time.time() - self.startup_time,
            "performance_stats": {},
            "errors": []
        }
        
        try:
            # Check LLM connection
            llm_test = self.llm_handler.test_connection_optimized()
            health["llm_connection"] = llm_test.get('connected', False) and llm_test.get('model_available', False)
            if not health["llm_connection"]:
                health["errors"].append(f"LLM: {llm_test.get('error', 'Unknown error')}")
            
            # Check vector store
            vs_health = self.vector_store.health_check()
            health["vector_store_healthy"] = vs_health.get('can_search', False) and vs_health.get('can_add', False)
            if not health["vector_store_healthy"]:
                health["errors"].extend([f"VectorStore: {err}" for err in vs_health.get('errors', [])])
            
            # Check retriever
            health["retriever_ready"] = self.retriever is not None
            if not health["retriever_ready"]:
                health["errors"].append("Retriever: Not initialized")
            
            # Get stats
            health["total_documents"] = self.vector_store.get_collection_stats().get('total_chunks', 0)
            health["performance_stats"] = {
                "llm": self.llm_handler.get_performance_stats(),
                "vector_store": self.vector_store.get_collection_stats()
            }
            
            if self.retriever:
                health["performance_stats"]["retriever"] = self.retriever.get_retrieval_stats()
            
        except Exception as e:
            health["errors"].append(f"Health check failed: {str(e)}")
        
        return health
    
    def optimize_for_batch_processing(self):
        """Optimize system for batch processing workloads"""
        print("⚡ Optimizing for batch processing...")
        self.llm_handler.optimize_for_batch_processing()
        
        if self.retriever:
            # Increase cache sizes for batch work
            self.retriever.cache_max_size = 500
            
        print("✅ System optimized for batch processing")
    
    def optimize_for_interactive(self):
        """Optimize system for interactive use"""
        print("⚡ Optimizing for interactive use...")
        self.llm_handler.optimize_for_interactive()
        
        if self.retriever:
            # Smaller cache, faster responses
            self.retriever.cache_max_size = 100
            
        print("✅ System optimized for interactive use")

def main():
    print("🚀 Starting Optimized Docu App...")
    
    app = OptimizedDocuApp()
    
    # Test all connections first
    print("🔌 Testing system health...")
    health = app.get_system_health()
    
    if not health["llm_connection"]:
        print("❌ LLM connection failed! Please make sure Ollama is running:")
        print("   Run: ollama serve")
        return
    
    # Create directories
    os.makedirs("./data/documents", exist_ok=True)
    os.makedirs("./data/chroma_db", exist_ok=True)
    
    # Interactive menu
    while True:
        print("\n" + "="*60)
        print("🤖 Optimized Docu RAG System")
        print("="*60)
        print("1. 💬 Simple Chat (LLM only)")
        print("2. 📚 Set up/Update Document Q&A")
        print("3. ❓ Ask question about documents")
        print("4. 📊 System Health & Performance Stats")
        print("5. ⚡ Optimize for Batch Processing")
        print("6. 🎯 Optimize for Interactive Use")  
        print("7. 🔍 Run Performance Test")
        print("8. 🚪 Exit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == "1":
            print("\n💬 Chat Mode (type 'exit' to return)")
            while True:
                user_input = input("\nYou: ")
                if user_input.lower() == 'exit':
                    break
                
                start_time = time.time()
                response = app.simple_chat_optimized(user_input)
                response_time = time.time() - start_time
                
                print(f"\n🤖 Assistant ({response_time:.2f}s): {response}")
        
        elif choice == "2":
            success = app.setup_optimized_rag_system()
            if success:
                print("✅ Document Q&A system ready!")
            else:
                print("❌ Setup failed!")
        
        elif choice == "3":
            if not app.retriever:
                print("❌ Please set up Document Q&A first (option 2)")
                continue
                
            question = input("\n❓ Your question: ")
            if question.strip():
                result = app.ask_question_optimized(question)
                
                print(f"\n🤖 Answer (confidence: {result['confidence']:.2f}):")
                print(f"📄 {result['answer']}")
                print(f"⏱️  Response time: {result['response_time']:.2f}s")
                print(f"📚 Documents used: {result['num_docs_used']}")
                
                if 'warning' in result:
                    print(f"⚠️  {result['warning']}")
        
        elif choice == "4":
            health = app.get_system_health()
            
            print(f"\n📊 System Health Report")
            print(f"🔌 LLM Connected: {'✅' if health['llm_connection'] else '❌'}")
            print(f"🗄️  Vector Store: {'✅' if health['vector_store_healthy'] else '❌'}")
            print(f"🔍 Retriever Ready: {'✅' if health['retriever_ready'] else '❌'}")
            print(f"📚 Total Documents: {health['total_documents']}")
            print(f"⏰ Uptime: {health['system_uptime']:.1f} seconds")
            
            if health['errors']:
                print(f"\n❌ Errors:")
                for error in health['errors']:
                    print(f"   • {error}")
            
            # Performance stats
            if health['performance_stats'].get('llm'):
                llm_stats = health['performance_stats']['llm']
                print(f"\n🤖 LLM Performance:")
                print(f"   • Cache Hit Rate: {llm_stats['cache_hit_rate']:.2%}")
                print(f"   • Avg Response Time: {llm_stats['average_response_time']:.2f}s")
                print(f"   • Total Requests: {llm_stats['total_requests']}")
        
        elif choice == "5":
            app.optimize_for_batch_processing()
        
        elif choice == "6":
            app.optimize_for_interactive()
            
        elif choice == "7":
            print("\n🔍 Running Performance Test...")
            # Simple performance test
            test_questions = [
                "What is Python?",
                "How do I install packages?", 
                "Database optimization tips"
            ]
            
            total_time = 0
            for i, question in enumerate(test_questions, 1):
                print(f"   Test {i}/3: {question}")
                start = time.time()
                result = app.ask_question_optimized(question)
                duration = time.time() - start
                total_time += duration
                print(f"   ✅ Completed in {duration:.2f}s")
            
            avg_time = total_time / len(test_questions)
            print(f"\n📊 Performance Test Results:")
            print(f"   • Average response time: {avg_time:.2f}s")
            print(f"   • Total test time: {total_time:.2f}s")
            
            if avg_time < 10:
                print("   🚀 Excellent performance!")
            elif avg_time < 20:
                print("   ✅ Good performance!")
            else:
                print("   ⚠️  Consider system optimization")
        
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-8.")

if __name__ == "__main__":
    main()
    