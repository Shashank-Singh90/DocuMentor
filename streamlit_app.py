import streamlit as st
import os
from pathlib import Path
import tempfile
from dotenv import load_dotenv
from src.llm_handler import LLMHandler
from src.document_processor import DocumentProcessor
from langchain.chains import RetrievalQA

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Docu - LangChain & Ollama",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "llm_handler" not in st.session_state:
    st.session_state.llm_handler = None
if "doc_processor" not in st.session_state:
    st.session_state.doc_processor = None
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "documents_processed" not in st.session_state:
    st.session_state.documents_processed = False

def initialize_handlers():
    """Initialize LangChain components"""
    try:
        if st.session_state.llm_handler is None:
            with st.spinner("Initializing LLM Handler..."):
                st.session_state.llm_handler = LLMHandler()
        
        if st.session_state.doc_processor is None:
            with st.spinner("Initializing Document Processor..."):
                st.session_state.doc_processor = DocumentProcessor()
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return False

def test_connection():
    """Test Ollama connection"""
    if st.session_state.llm_handler:
        try:
            response = st.session_state.llm_handler.llm.invoke("Hello")
            return True, response
        except Exception as e:
            return False, str(e)
    return False, "LLM Handler not initialized"

def process_uploaded_files(uploaded_files):
    """Process uploaded files and create vector store"""
    if not uploaded_files:
        return False, "No files uploaded"
    
    try:
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded files
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Load and process documents
        with st.spinner("Loading documents..."):
            documents = st.session_state.doc_processor.load_documents(temp_dir)
        
        if not documents:
            return False, "No documents could be loaded"
        
        with st.spinner("Processing documents..."):
            processed_docs = st.session_state.doc_processor.process_documents(documents)
        
        with st.spinner("Creating vector store..."):
            vector_store = st.session_state.doc_processor.create_vector_store(processed_docs)
        
        with st.spinner("Setting up QA chain..."):
            st.session_state.qa_chain = RetrievalQA.from_chain_type(
                llm=st.session_state.llm_handler.llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=True
            )
        
        st.session_state.documents_processed = True
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir)
        
        return True, f"Successfully processed {len(documents)} documents into {len(processed_docs)} chunks"
    
    except Exception as e:
        return False, f"Error processing documents: {str(e)}"

def main():
    # Header
    st.title("📚 Docu - LangChain & Ollama Integration")
    st.markdown("Local document Q&A powered by LangChain and Ollama")
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Configuration")
        
        # Initialize button
        if st.button("🔌 Initialize System", type="primary"):
            if initialize_handlers():
                st.success("System initialized successfully!")
            else:
                st.error("Failed to initialize system")
        
        # Connection test
        if st.session_state.llm_handler:
            if st.button("🧪 Test Connection"):
                is_connected, response = test_connection()
                if is_connected:
                    st.success("✅ Connection successful!")
                    st.info(f"Response: {response[:100]}...")
                else:
                    st.error(f"❌ Connection failed: {response}")
        
        st.divider()
        
        # Model info
        model_name = os.getenv('OLLAMA_MODEL', 'gemma2:2b')
        st.info(f"🤖 Model: {model_name}")
        st.info(f"🔗 Ollama URL: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
    
    # Main content tabs
    tab1, tab2 = st.tabs(["💬 Simple Chat", "📄 Document Q&A"])
    
    with tab1:
        st.header("Simple Chat")
        st.markdown("Chat directly with your local model")
        
        if not st.session_state.llm_handler:
            st.warning("⚠️ Please initialize the system first using the sidebar")
        else:
            # Chat interface
            if prompt := st.chat_input("Type your message..."):
                # Add user message to chat history
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # Get response
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.llm_handler.generate_response(prompt)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Clear chat button
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    with tab2:
        st.header("Document Q&A")
        st.markdown("Upload documents and ask questions about them")
        
        if not st.session_state.llm_handler or not st.session_state.doc_processor:
            st.warning("⚠️ Please initialize the system first using the sidebar")
        else:
            # File upload
            uploaded_files = st.file_uploader(
                "Upload documents",
                type=['txt', 'pdf'],
                accept_multiple_files=True,
                help="Upload PDF or text files to analyze"
            )
            
            # Process documents button
            if uploaded_files and st.button("📊 Process Documents", type="primary"):
                success, message = process_uploaded_files(uploaded_files)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            
            # Use existing test documents
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**Or use existing test documents:**")
            with col2:
                if st.button("📋 Use Test Docs"):
                    if os.path.exists("./data/documents"):
                        try:
                            documents = st.session_state.doc_processor.load_documents("./data/documents")
                            processed_docs = st.session_state.doc_processor.process_documents(documents)
                            vector_store = st.session_state.doc_processor.create_vector_store(processed_docs)
                            
                            st.session_state.qa_chain = RetrievalQA.from_chain_type(
                                llm=st.session_state.llm_handler.llm,
                                chain_type="stuff",
                                retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
                                return_source_documents=True
                            )
                            st.session_state.documents_processed = True
                            st.success(f"Loaded {len(documents)} test documents")
                        except Exception as e:
                            st.error(f"Error loading test documents: {str(e)}")
                    else:
                        st.error("Test documents not found")
            
            # Q&A Interface
            if st.session_state.documents_processed and st.session_state.qa_chain:
                st.success("📚 Documents are ready for Q&A!")
                
                # Question input
                question = st.text_input("Ask a question about your documents:")
                
                if question and st.button("🔍 Get Answer"):
                    with st.spinner("Searching documents..."):
                        try:
                            result = st.session_state.qa_chain({"query": question})
                            
                            # Display answer
                            st.markdown("### 📝 Answer:")
                            st.write(result["result"])
                            
                            # Display sources
                            if "source_documents" in result and result["source_documents"]:
                                st.markdown("### 📚 Sources:")
                                for i, doc in enumerate(result["source_documents"]):
                                    with st.expander(f"Source {i+1}"):
                                        st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                                        if hasattr(doc, 'metadata') and doc.metadata:
                                            st.caption(f"Metadata: {doc.metadata}")
                        
                        except Exception as e:
                            st.error(f"Error answering question: {str(e)}")
                
                # Suggested questions
                st.markdown("### 💡 Try these questions:")
                suggestions = [
                    "What is LangChain used for?",
                    "How do you combine LangChain with Ollama?",
                    "What are the features of the Docu project?",
                    "What models does Ollama support?"
                ]
                
                cols = st.columns(2)
                for i, suggestion in enumerate(suggestions):
                    with cols[i % 2]:
                        if st.button(suggestion, key=f"suggestion_{i}"):
                            with st.spinner("Searching documents..."):
                                try:
                                    result = st.session_state.qa_chain({"query": suggestion})
                                    st.markdown("### 📝 Answer:")
                                    st.write(result["result"])
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            
            elif not st.session_state.documents_processed:
                st.info("👆 Please upload and process documents first")

if __name__ == "__main__":
    main()
