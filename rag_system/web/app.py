"""
DocuMentor - Documentation Assistant
"""

import streamlit as st
import time
import os
from typing import Dict, List, Optional
from pathlib import Path

# Import core components
from rag_system.core import DocumentChunker, VectorStore, get_logger
from rag_system.core.processing import document_processor
from rag_system.core.generation.llm_handler import llm_service
from rag_system.core.search import web_search_provider
from rag_system.config import get_settings

logger = get_logger(__name__)

# Technology mapping
TECHNOLOGY_MAPPING = {
    'python': 'Python 3.13',
    'fastapi': 'FastAPI',
    'django': 'Django 5.0',
    'react_nextjs': 'React & Next.js',
    'nodejs': 'Node.js',
    'postgresql': 'PostgreSQL',
    'mongodb': 'MongoDB',
    'typescript': 'TypeScript',
    'langchain': 'LangChain'
}

def load_css():
    """Load custom CSS"""
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def configure_page():
    """Configure Streamlit page"""
    st.set_page_config(
        page_title="DocuMentor",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    load_css()

def initialize_rag_system():
    """Initialize system components"""
    try:
        settings = get_settings()
        vector_store = VectorStore()
        chunker = DocumentChunker()

        # Session state init
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        return {
            'status': 'success',
            'vector_store': vector_store,
            'chunker': chunker,
            'document_processor': document_processor,
            'settings': settings
        }

    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        return {'status': 'error', 'error': str(e)}

def render_sidebar(components: Dict):
    """Render sidebar controls"""
    with st.sidebar:
        st.header("Controls")
        
        # Status
        if components.get('status') == 'success':
            st.success("System Operational")
        else:
            st.error(f"System Error: {components.get('error')}")
            return {}

        # LLM Provider
        available_providers = llm_service.get_available_providers()
        if available_providers:
            current_provider = st.selectbox(
                "Model Provider",
                available_providers,
                index=available_providers.index(llm_service.current_provider)
                if llm_service.current_provider in available_providers else 0
            )
            
            if current_provider != llm_service.current_provider:
                if llm_service.set_provider(current_provider):
                    st.toast(f"Switched to {current_provider}")

        # Mode Selection
        response_mode = st.radio(
            "Response Mode",
            ["Standard", "Code Generation", "Detailed Sources"]
        )

        st.subheader("Search Settings")
        search_k = st.slider("Documents to retrieve", 3, 15, 8)
        enable_web_search = st.checkbox("Web Search", value=True)
        
        # Tech Filter
        tech_options = ["All"] + list(TECHNOLOGY_MAPPING.values())
        selected_tech = st.selectbox("Technology Filter", tech_options)
        
        technology_filter = None
        if selected_tech != "All":
            for k, v in TECHNOLOGY_MAPPING.items():
                if v == selected_tech:
                    technology_filter = {"technology": k}
                    break

        # Document Upload
        with st.expander("Upload Documents"):
            uploaded_files = st.file_uploader(
                "Upload files", 
                accept_multiple_files=True
            )
            if uploaded_files and st.button("Process"):
                process_uploads(uploaded_files, components)

        return {
            'search_k': search_k,
            'enable_web_search': enable_web_search,
            'technology_filter': technology_filter,
            'selected_tech_name': selected_tech,
            'response_mode': response_mode,
            'chunk_overlap': 2
        }

def process_uploads(uploaded_files, components):
    """Handle file uploads"""
    count = 0
    with st.spinner("Processing..."):
        for file in uploaded_files:
            try:
                content = file.read()
                result = components['document_processor'].process_file(file.name, content)
                if result['success']:
                    doc = {
                        'title': file.name, 
                        'content': result['content'], 
                        'source': 'user_upload'
                    }
                    chunks = components['chunker'].chunk_document(doc)
                    if chunks:
                        texts = [c['content'] for c in chunks]
                        metas = [c['metadata'] for c in chunks]
                        ids = [f"upload_{file.name}_{i}" for i in range(len(chunks))]
                        components['vector_store'].add_documents(texts, metas, ids)
                        count += 1
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
    
    if count > 0:
        st.success(f"Processed {count} files")
        time.sleep(1)
        st.rerun()

def main():
    configure_page()
    components = initialize_rag_system()
    
    st.markdown('<div class="main-header"><h1>DocuMentor</h1></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Developer Documentation Assistant</p>', unsafe_allow_html=True)

    ui_settings = render_sidebar(components)
    
    if not ui_settings:
        return

    # Main Chat Interface
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg:
                with st.expander("Sources"):
                    for s in msg["sources"]:
                        st.markdown(f"- {s.get('metadata', {}).get('title', 'Unknown')}")

    if prompt := st.chat_input("Ask a question..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = generate_response(prompt, ui_settings, components)
                st.markdown(response['answer'])
                
                if response.get('sources'):
                    with st.expander("Sources used"):
                        for s in response['sources'][:5]:
                            meta = s.get('metadata', {})
                            st.markdown(f"- **{meta.get('title', 'Untitled')}** ({meta.get('technology', 'General')})")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response['answer'],
                    "sources": response.get('sources', [])
                })

def generate_response(question: str, settings: Dict, components: Dict) -> Dict:
    """Generate response based on settings"""
    try:
        # Build filters
        filter_dict = settings['technology_filter']
        
        # Search
        search_results = []
        if settings['response_mode'] != "Web Only":
            search_results = components['vector_store'].search(
                question,
                k=settings['search_k'],
                filter_dict=filter_dict
            )

        if settings['enable_web_search']:
            search_results.extend(web_search_provider.search_web(question, max_results=3))

        # Generate
        if settings['response_mode'] == "Code Generation":
            prompt = f"Provide a complete code implementation for: {question}"
            if settings['selected_tech_name'] != "All":
                 prompt = f"Using {settings['selected_tech_name']}, {prompt}"
            
            answer = llm_service.generate_code(prompt, "python", search_results)
            if "```" not in answer:
                answer = f"```python\n{answer}\n```"
        else:
            answer = llm_service.generate_answer(f"Question: {question}", search_results)

        return {
            'answer': answer,
            'sources': search_results
        }
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return {'answer': f"Sorry, I encountered an error: {str(e)}"}

if __name__ == "__main__":
    main()