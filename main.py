import os
from dotenv import load_dotenv
from src.llm_handler import LLMHandler
from src.document_processor import DocumentProcessor
from langchain.chains import RetrievalQA

load_dotenv()

class DocuApp:
    def __init__(self):
        self.llm_handler = LLMHandler()
        self.doc_processor = DocumentProcessor()
        self.qa_chain = None
    
    def setup_rag_system(self, documents_folder: str = "./data/documents"):
        """Set up optimized RAG system"""
        print("📚 Loading documents...")
        documents = self.doc_processor.load_documents(documents_folder)
        
        if not documents:
            print("❌ No documents found!")
            return False
        
        print("✂️ Processing documents...")
        processed_docs = self.doc_processor.process_documents(documents)
        
        print("🗄️ Creating vector store...")
        vector_store = self.doc_processor.create_vector_store(processed_docs)
        
        print("🔗 Setting up optimized QA chain...")
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm_handler.llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_type="mmr",  # Maximum Marginal Relevance
                search_kwargs={
                    "k": 3,         # Top 3 relevant chunks
                    "lambda_mult": 0.7  # Balance relevance vs diversity
                }
            ),
            return_source_documents=True
        )
        
        print("✅ Optimized RAG system ready!")
        return True
    
    def ask_question(self, question: str):
        """Ask question with quality assurance"""
        if not self.qa_chain:
            return "Please set up the RAG system first."
        
        try:
            result = self.qa_chain({"query": question})
            return {
                "answer": result["result"],
                "sources": result["source_documents"]
            }
        except Exception as e:
            return f"Error: {str(e)}"
    
    def simple_chat(self, message: str):
        """Simple chat with quality check"""
        return self.llm_handler.generate_response(message)

def main():
    print("🚀 Starting Optimized Docu App...")
    
    app = DocuApp()
    
    # Test connection
    print("🔌 Testing connection...")
    if not app.llm_handler.test_connection():
        print("❌ Please make sure Ollama is running!")
        return
    
    # Create directories
    os.makedirs("./data/documents", exist_ok=True)
    os.makedirs("./data/chroma_db", exist_ok=True)
    
    while True:
        print("\n" + "="*50)
        print("1. Simple Chat")
        print("2. Set up Document Q&A")
        print("3. Ask question about documents")
        print("4. Exit")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == "1":
            message = input("You: ")
            print(f"Bot: {app.simple_chat(message)}")
        
        elif choice == "2":
            docs_folder = input("Documents folder (default: ./data/documents): ").strip()
            if not docs_folder:
                docs_folder = "./data/documents"
            app.setup_rag_system(docs_folder)
        
        elif choice == "3":
            if not app.qa_chain:
                print("❌ Please set up Document Q&A first!")
                continue
            
            question = input("Your question: ")
            result = app.ask_question(question)
            
            if isinstance(result, dict):
                print(f"\n📝 Answer: {result['answer']}")
                print(f"📚 Sources used: {len(result['sources'])} documents")
            else:
                print(f"❌ {result}")
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
