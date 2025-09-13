import streamlit as st
import time
from pathlib import Path
import os
from typing import Dict, List

# Import our modules
from src.retrieval.vector_store import ChromaVectorStore
from src.generation.llm_handler import SimpleLLMHandler
from src.utils.logger import get_logger
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title="DocuMentor - AI Documentation Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
# Custom CSS - REPLACE THE EXISTING CSS SECTION
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background-color: #ffffff;
    }
    
    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #42A5F5, #64B5F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        text-align: center;
        color: #333333;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Text visibility fixes */
    .stMarkdown, .stText, p, span, div {
        color: #333333 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #1976D2 !important;
    }
    
    /* Source cards */
    .source-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #42A5F5;
        color: #333333;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Chat messages */
    .user-message {
        background-color: #e3f2fd;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        margin-left: 10%;
        color: #333333;
        border: 1px solid #bbdefb;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        margin-right: 10%;
        color: #333333;
        border: 1px solid #e0e0e0;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #42A5F5;
        color: white !important;
        border-radius: 0.5rem;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #1976D2;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: white;
        color: #333333;
        border: 2px solid #e0e0e0;
        border-radius: 0.5rem;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: white;
        color: #333333;
    }
    
    /* Sidebar text */
    .css-1d391kg .stMarkdown {
        color: #333333 !important;
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background-color: #f0f7ff;
        border: 1px solid #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #333333;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #e3f2fd;
        color: #333333;
    }
    
    /* Success boxes */
    .stSuccess {
        background-color: #e8f5e8;
        color: #333333;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: #fff3cd;
        color: #333333;
    }
    
    /* Error boxes */
    .stError {
        background-color: #f8d7da;
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize logger
logger = get_logger(__name__)

@st.cache_resource
def initialize_components():
    """Initialize all components"""
    with st.spinner("🚀 Initializing DocuMentor components..."):
        try:
            # Initialize vector store
            vector_store = ChromaVectorStore()
            
            # Initialize LLM handler - try Ollama first, fallback to Simple
            try:
                from src.generation.ollama_handler import OllamaLLMHandler
                llm_handler = OllamaLLMHandler()
                logger.info("🤖 Using Ollama LLM Handler")
            except Exception as e:
                logger.warning(f"⚠️ Ollama not available: {e}")
                llm_handler = SimpleLLMHandler()
                logger.info("🔄 Using Simple LLM Handler")
            
            logger.info("✅ All components initialized successfully")
            
            return {
                'vector_store': vector_store,
                'llm_handler': llm_handler,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

def search_and_respond(query: str, vector_store: ChromaVectorStore, llm_handler: SimpleLLMHandler, k: int = 5, filters: dict = None) -> Dict:
    """Search for relevant information and generate response"""
    start_time = time.time()
    
    try:
        # Search for relevant chunks
        search_results = vector_store.search(query, k=k, filter_dict=filters)
        
        if not search_results:
            return {
                'answer': f"I couldn't find specific information about '{query}' in the available documentation. Try rephrasing your question or check if it's related to LangChain or FastAPI topics.",
                'sources': [],
                'search_results': [],
                'response_time': time.time() - start_time,
                'confidence': 0.0
            }
        
        # Generate answer using LLM
        answer = llm_handler.generate_answer(query, search_results)
        
        # Calculate confidence (average of top 3 scores)
        top_scores = [r.get('score', 0) for r in search_results[:3]]
        confidence = sum(top_scores) / len(top_scores) if top_scores else 0.0
        
        # Format sources
        sources = []
        for result in search_results:
            metadata = result.get('metadata', {})
            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'source': metadata.get('source', 'unknown'),
                'url': metadata.get('url', '#'),
                'score': result.get('score', 0),
                'content_preview': result.get('content', '')[:200] + '...'
            })
        
        return {
            'answer': answer,
            'sources': sources,
            'search_results': search_results,
            'response_time': time.time() - start_time,
            'confidence': confidence
        }
        
    except Exception as e:
        logger.error(f"❌ Error in search_and_respond: {e}")
        return {
            'answer': f"Sorry, I encountered an error while processing your question: {str(e)}",
            'sources': [],
            'search_results': [],
            'response_time': time.time() - start_time,
            'confidence': 0.0
        }

def main():
    """Main application"""
    # Header
    st.markdown('<h1 class="main-header">🧠 DocuMentor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Documentation Assistant for LangChain & FastAPI</p>', unsafe_allow_html=True)
    
    # Initialize components
    components = initialize_components()
    
    if components['status'] == 'error':
        st.error(f"❌ Failed to initialize DocuMentor: {components['error']}")
        st.info("💡 Make sure you've run the setup scripts to create the vector database.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Search settings
        st.subheader("🔍 Search Settings")
        search_k = st.slider("Number of results", min_value=3, max_value=10, value=5)
        
        # Filter options
        st.subheader("🏷️ Filters")
        doc_source = st.selectbox(
            "Documentation Source",
            options=["All", "LangChain", "FastAPI"],
            index=0
        )
        
        doc_type = st.selectbox(
            "Document Type",
            options=["All", "Tutorial", "API Reference", "Conceptual"],
            index=0
        )
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            show_sources = st.checkbox("Show detailed sources", value=True)
            show_confidence = st.checkbox("Show confidence scores", value=True)
            show_timing = st.checkbox("Show response timing", value=True)
        
        # Statistics
        st.subheader("📊 Knowledge Base Stats")
        try:
            stats = components['vector_store'].get_collection_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Chunks", f"{stats.get('total_chunks', 0):,}")
            with col2:
                st.metric("Sources", len(stats.get('sources', {})))
            
            # Show source breakdown
            if 'sources' in stats:
                st.write("**Source Breakdown:**")
                for source, count in stats['sources'].items():
                    st.write(f"• {source.upper()}: {count} chunks")
                    
        except Exception as e:
            st.error(f"Could not load stats: {e}")
        
        # LLM Status
        # Document Upload Section
        st.subheader("📁 Upload Your Documents")
        
        with st.expander("📤 Upload Markdown, CSV, or Text Files", expanded=False):
            uploaded_file = st.file_uploader(
                "Choose a file to add to your knowledge base",
                type=['md', 'markdown', 'csv', 'txt'],
                help="Upload Markdown, CSV, or Text files to expand DocuMentor's knowledge"
            )
            
            if uploaded_file is not None:
                # Show file details
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Size:** {uploaded_file.size} bytes")
                st.write(f"**Type:** {uploaded_file.type}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Process & Add to Knowledge Base", use_container_width=True):
                        try:
                            with st.spinner("📖 Processing your document..."):
                                # Import the document processor
                                import sys
                                sys.path.append('src')
                                from ingestion.document_processor import DocumentProcessor
                                
                                # Get file extension
                                file_extension = uploaded_file.name.split('.')[-1].lower()
                                
                                # Read file content
                                file_content = uploaded_file.read()
                                
                                # Process the document
                                processor = DocumentProcessor()
                                chunks = processor.process_uploaded_file(
                                    file_content, 
                                    uploaded_file.name, 
                                    file_extension
                                )
                                
                                if chunks:
                                    # Add to vector store
                                    texts = [chunk['content'] for chunk in chunks]
                                    metadatas = [chunk['metadata'] for chunk in chunks]
                                    ids = [f"upload_{uploaded_file.name}_{i}_{hash(chunk['content']) % 10000}" 
                                          for i, chunk in enumerate(chunks)]
                                    
                                    # Add to vector store using the same method that worked before
                                    added_count = 0
                                    for text, metadata, doc_id in zip(texts, metadatas, ids):
                                        try:
                                            if hasattr(components['vector_store'], 'add'):
                                                components['vector_store'].add(
                                                    text=text,
                                                    metadata=metadata,
                                                    doc_id=doc_id
                                                )
                                            elif hasattr(components['vector_store'], 'collection'):
                                                components['vector_store'].collection.add(
                                                    documents=[text],
                                                    metadatas=[metadata],
                                                    ids=[doc_id]
                                                )
                                            added_count += 1
                                        except Exception as e:
                                            logger.warning(f"Error adding chunk: {e}")
                                            continue
                                    
                                    # Success message
                                    st.success(f"✅ Successfully added {added_count} chunks from {uploaded_file.name}!")
                                    st.info("🔄 The document is now part of your knowledge base. You can ask questions about it!")
                                    
                                    # Show preview of what was added
                                    with st.expander("📋 Preview of Added Content"):
                                        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                                            st.write(f"**Chunk {i+1}: {chunk['metadata']['title']}**")
                                            st.write(chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'])
                                            st.write("---")
                                        
                                        if len(chunks) > 3:
                                            st.write(f"... and {len(chunks) - 3} more chunks")
                                else:
                                    st.error("❌ Could not process the file. Please check the format.")
                                    
                        except Exception as e:
                            st.error(f"❌ Error processing file: {str(e)}")
                            logger.error(f"Upload processing error: {e}")
                
                with col2:
                    if st.button("👀 Preview Content", use_container_width=True):
                        try:
                            # Show file preview
                            file_content = uploaded_file.read()
                            
                            if uploaded_file.name.endswith(('.md', '.markdown', '.txt')):
                                content_str = file_content.decode('utf-8')
                                st.text_area("File Preview:", content_str[:1000], height=200)
                                if len(content_str) > 1000:
                                    st.info("Showing first 1000 characters...")
                            
                            elif uploaded_file.name.endswith('.csv'):
                                import pandas as pd
                                import io
                                df = pd.read_csv(io.BytesIO(file_content))
                                st.write("**CSV Preview:**")
                                st.dataframe(df.head(10))
                                st.info(f"Total rows: {len(df)}, Columns: {len(df.columns)}")
                            
                            # Reset file pointer
                            uploaded_file.seek(0)
                            
                        except Exception as e:
                            st.error(f"Error previewing file: {str(e)}")
        st.subheader("🤖 AI Model Status")
        try:
            if hasattr(components['llm_handler'], 'check_model_status'):
                status = components['llm_handler'].check_model_status()
                if status['status'] == 'available':
                    st.success(f"✅ {status['model']} Ready")
                elif status['status'] == 'model_not_found':
                    st.warning("⚠️ Model not found")
                    st.info("Run: `ollama pull llama3.2:3b`")
                else:
                    st.error("❌ Ollama not running")
                    st.info("Install Ollama from ollama.ai")
            else:
                st.info("📝 Using Simple Demo Handler")
        except Exception as e:
            st.error(f"Error checking LLM status: {e}")
        
        # Sample questions
        st.subheader("💡 Try These Questions")
        sample_questions = [
            "What is LangChain?",
            "How to create a FastAPI application?",
            "LangChain agents tutorial",
            "FastAPI authentication examples",
            "Compare LangChain and FastAPI",
            "Building chatbots with LangChain"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{hash(question)}"):
                st.session_state.sample_question = question
    
    # Initialize session state for chat
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'sample_question' in st.session_state:
        # Auto-fill the sample question
        user_input = st.session_state.sample_question
        del st.session_state.sample_question
    else:
        user_input = None
    
    # Main chat interface
    st.subheader("💬 Ask DocuMentor Anything")
    
    # Chat input
    query = st.text_input(
        "Ask about LangChain or FastAPI:",
        value=user_input if user_input else "",
        placeholder="e.g., How do I create a FastAPI application with authentication?",
        key="chat_input"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ask_button = st.button("🚀 Ask DocuMentor", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear Chat", use_container_width=True)
    with col3:
        example_button = st.button("🎲 Random Example", use_container_width=True)
    
    # Handle button clicks
    if clear_button:
        st.session_state.messages = []
        st.rerun()
    
    if example_button:
        import random
        random_question = random.choice(sample_questions)
        st.session_state.sample_question = random_question
        st.rerun()
    
    # Process query
    if ask_button and query:
        # Prepare filters
        filters = None
        if doc_source != "All":
            filters = {"source": doc_source.lower()}
        elif doc_type != "All":
            filters = {"doc_type": doc_type.lower().replace(" ", "_")}
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Generate response
        with st.spinner("🤔 Thinking..."):
            response = search_and_respond(
                query=query,
                vector_store=components['vector_store'],
                llm_handler=components['llm_handler'],
                k=search_k,
                filters=filters if filters else None
            )
        
        # Add assistant response to chat
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response['answer'],
            "sources": response['sources'],
            "response_time": response['response_time'],
            "confidence": response['confidence']
        })
    
    # Display chat history
    if st.session_state.messages:
        st.subheader("📚 Conversation")
        
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>DocuMentor:</strong><br>
                    {message["content"].replace('\n', '<br>')}
                </div>
                """, unsafe_allow_html=True)
                
                # Show additional info
                col1, col2, col3 = st.columns(3)
                
                if show_timing and "response_time" in message:
                    with col1:
                        st.metric("Response Time", f"{message['response_time']:.2f}s")
                
                if show_confidence and "confidence" in message:
                    with col2:
                        st.metric("Confidence", f"{message['confidence']:.0%}")
                
                if "sources" in message:
                    with col3:
                        st.metric("Sources Found", len(message["sources"]))
                
                # Show detailed sources
                if show_sources and "sources" in message and message["sources"]:
                    with st.expander(f"📚 Sources ({len(message['sources'])} found)", expanded=False):
                        for j, source in enumerate(message["sources"][:5]):  # Show top 5
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>{j+1}. {source['title']}</strong><br>
                                <small>{source['source'].upper()} | Relevance: {source['score']:.2%}</small><br>
                                <em>{source['content_preview']}</em>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
    
    else:
        # Welcome message
        st.info("""
        👋 **Welcome to DocuMentor!**
        
        I'm your AI assistant for LangChain and FastAPI documentation. Here's what I can help you with:
        
        • **Explain concepts** - "What is LangChain?"
        • **Provide tutorials** - "How to create a FastAPI app?"
        • **Show examples** - "FastAPI authentication examples"
        • **Compare technologies** - "LangChain vs other frameworks"
        
        Try asking a question above or click on the sample questions in the sidebar! 🚀
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🧠 <strong>DocuMentor</strong> - Built with LangChain, FastAPI, ChromaDB, and Streamlit<br>
        <small>Powered by semantic search and intelligent document retrieval</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()