"""
Enhanced Professional Streamlit Application for RAG System v2
With improved performance, advanced code generation, and detailed source filtering
"""

import streamlit as st
import time
import os
from typing import Dict, List, Optional
from pathlib import Path

# Import core components
from rag_system.core import SmartChunker, VectorStore, get_logger
from rag_system.core.processing import document_processor
from rag_system.core.generation.llm_handler import enhanced_llm_handler
from rag_system.core.search import web_search_provider
from rag_system.config import get_settings

# Technology mapping for better filtering
TECHNOLOGY_MAPPING = {
    'python': 'Python 3.13.5',
    'fastapi': 'FastAPI',
    'django': 'Django 5.2',
    'react_nextjs': 'React & Next.js',
    'nodejs': 'Node.js',
    'postgresql': 'PostgreSQL',
    'mongodb': 'MongoDB',
    'typescript': 'TypeScript',
    'langchain': 'LangChain'
}

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="DocuMentor - AI-Powered Documentation Assistant",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize dark mode in session state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    # Enhanced Modern CSS with Dark/Light Mode Support
    dark_mode = st.session_state.get('dark_mode', False)

    if dark_mode:
        # Dark mode styles
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            .stApp {
                font-family: 'Inter', sans-serif;
                background-color: #0e1117;
                color: #ffffff;
            }

            /* Dark mode main header */
            .main-header {
                font-size: 3.5rem;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                padding: 2rem 0;
                margin-bottom: 2rem;
                letter-spacing: -0.02em;
            }

            .subtitle {
                text-align: center;
                color: #9ca3af;
                font-size: 1.2rem;
                font-weight: 400;
                margin-bottom: 3rem;
            }

            /* Dark mode components */
            .sidebar-section {
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }

            .tech-badge {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.4rem 1rem;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 500;
                margin: 0.3rem;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }

            .source-card {
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }

            .metric-card {
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 0.5rem 0;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }

            .chat-message {
                background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }

            /* Dark mode sidebar */
            .css-1d391kg {
                background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
            }

            /* Dark mode status indicators */
            .status-indicator {
                display: inline-flex;
                align-items: center;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 1rem;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light mode styles
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            .stApp {
                font-family: 'Inter', sans-serif;
                background-color: #ffffff;
                color: #1f2937;
            }

        .main-header {
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            padding: 2rem 0;
            margin-bottom: 2rem;
            letter-spacing: -0.02em;
        }

        .subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 1.2rem;
            font-weight: 400;
            margin-bottom: 3rem;
        }

        .tech-badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            margin: 0.3rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
        }

        .tech-badge:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .source-card {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }

        .source-card:hover {
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            transform: translateY(-2px);
        }

        .code-container {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #404040;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }

        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transform: translateY(-1px);
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }

        .status-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }

        .status-error {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        }

        .response-mode-indicator {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .mode-smart {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }
        .mode-code {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }
        .mode-detailed {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        }

        .chat-message {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }

        .sidebar-section {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .upload-area {
            border: 2px dashed #d1d5db;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
            transition: all 0.3s ease;
        }

        .upload-area:hover {
            border-color: #667eea;
            background: linear-gradient(135deg, #f0f7ff 0%, #e6f3ff 100%);
        }

        /* Custom button styles */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        }

        /* Input styling */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid #d1d5db;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        /* Loading spinner */
        .stSpinner {
            color: #667eea;
        }

        /* Expander styling */
        .streamlit-expander {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        /* Metric styling */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_enhanced_rag_system():
    """Initialize the enhanced RAG system components with error handling"""
    logger = get_logger()

    try:
        # Initialize settings
        settings = get_settings()

        # Initialize core components
        logger.info("Initializing enhanced RAG system components...")

        vector_store = VectorStore()
        chunker = SmartChunker()

        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        if 'advanced_mode' not in st.session_state:
            st.session_state.advanced_mode = False

        logger.info("Enhanced RAG system initialized successfully")

        return {
            'status': 'success',
            'vector_store': vector_store,
            'chunker': chunker,
            'document_processor': document_processor,
            'settings': settings
        }

    except Exception as e:
        logger.error(f"Failed to initialize enhanced RAG system: {e}")
        return {'status': 'error', 'error': str(e)}


def render_enhanced_sidebar(components: Dict):
    """Render enhanced sidebar with advanced controls"""
    with st.sidebar:
        st.header("📚 DocuMentor Controls")

        # Dark Mode Toggle
        with st.container():
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("🎨 Theme Settings")

            current_mode = "Dark Mode" if st.session_state.get('dark_mode', False) else "Light Mode"
            new_mode = st.selectbox(
                "Choose Theme:",
                ["Light Mode", "Dark Mode"],
                index=1 if st.session_state.get('dark_mode', False) else 0,
                help="Switch between light and dark themes"
            )

            if new_mode != current_mode:
                st.session_state.dark_mode = (new_mode == "Dark Mode")
                st.rerun()

            mode_icon = "🌙" if st.session_state.get('dark_mode', False) else "☀️"
            st.info(f"{mode_icon} Current theme: {current_mode}")
            st.markdown('</div>', unsafe_allow_html=True)

        # System Status with enhanced styling
        if components['status'] == 'success':
            st.markdown('<div class="status-indicator status-success">🚀 System Operational</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-indicator status-error">⚠️ System Error: {components.get("error", "Unknown")}</div>', unsafe_allow_html=True)
            return {}

        # LLM Provider Selection with enhanced UI
        with st.container():
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("🧠 AI Provider")
            available_providers = enhanced_llm_handler.get_available_providers()

            if available_providers:
                current_provider = st.selectbox(
                    "Select AI Provider",
                    available_providers,
                    index=available_providers.index(enhanced_llm_handler.current_provider)
                          if enhanced_llm_handler.current_provider in available_providers else 0,
                    help="Choose your preferred AI model provider"
                )

                if current_provider != enhanced_llm_handler.current_provider:
                    if enhanced_llm_handler.set_provider(current_provider):
                        st.success(f"✅ Switched to {current_provider}")
                    else:
                        st.error(f"❌ Failed to switch to {current_provider}")
            else:
                st.warning("⚠️ No AI providers available")
            st.markdown('</div>', unsafe_allow_html=True)

        # Enhanced Response Mode with better UX
        with st.container():
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("⚙️ Response Mode")
            response_mode = st.radio(
                "Choose response type:",
                ["Smart Answer", "Code Generation", "Detailed Sources"],
                help="🧠 Smart Answer: Balanced, comprehensive responses\n🔧 Code Generation: Focus on code implementation\n📖 Detailed Sources: Show all references and documentation",
                horizontal=False
            )

            # Show mode description
            mode_descriptions = {
                "Smart Answer": "🧠 Provides balanced, comprehensive responses with practical examples",
                "Code Generation": "🔧 Focuses on generating working code implementations with best practices",
                "Detailed Sources": "📖 Shows extensive documentation references and detailed explanations"
            }
            st.info(mode_descriptions[response_mode])
            st.markdown('</div>', unsafe_allow_html=True)

        # Advanced Search Settings
        st.subheader("🔍 Search Settings")
        search_k = st.slider("Results to retrieve", 3, 15, 8, help="More results = better context but slower response")
        enable_web_search = st.checkbox("Enable web search", value=True, help="Search the internet for additional context")

        # Technology-Specific Filtering
        st.subheader("🎯 Technology Filter")

        # Get available technologies from vector store
        try:
            stats = components['vector_store'].get_collection_stats()
            available_sources = list(stats.get('sources', {}).keys())

            # Create technology options
            tech_options = ["All Technologies"]

            # Add comprehensive docs technologies
            if 'comprehensive_docs' in available_sources:
                tech_options.extend([f"📚 {name}" for name in TECHNOLOGY_MAPPING.values()])

            # Add other sources
            for source in available_sources:
                if source not in ['comprehensive_docs']:
                    tech_options.append(f"📄 {source.replace('_', ' ').title()}")

            selected_tech = st.selectbox(
                "Filter by technology:",
                options=tech_options,
                help="Focus search on specific technologies"
            )

            # Create filter based on selection
            if selected_tech == "All Technologies":
                source_filter = None
                technology_filter = None
            elif selected_tech.startswith("📚"):
                # Technology-specific filter
                tech_name = selected_tech[2:]  # Remove emoji
                # Find the key for this technology
                tech_key = None
                for key, value in TECHNOLOGY_MAPPING.items():
                    if value == tech_name:
                        tech_key = key
                        break

                if tech_key:
                    technology_filter = {"technology": tech_key}
                    source_filter = {"source": "comprehensive_docs"}
                else:
                    technology_filter = None
                    source_filter = {"source": "comprehensive_docs"}
            else:
                # Other source filter
                source_name = selected_tech[2:].lower().replace(' ', '_')
                source_filter = {"source": source_name}
                technology_filter = None

        except Exception as e:
            st.warning(f"Could not load technology information: {e}")
            selected_tech = "All Technologies"
            source_filter = None
            technology_filter = None

        # Advanced Options
        with st.expander("🔧 Advanced Options"):
            chunk_overlap = st.slider("Search overlap", 0, 5, 2, help="Higher overlap = more comprehensive search")
            temperature = st.slider("Response creativity", 0.0, 1.0, 0.3, 0.1, help="Higher = more creative, Lower = more factual")
            max_tokens = st.slider("Response length", 100, 2000, 800, 50, help="Maximum response length")

            # Performance options
            st.write("**Performance Settings:**")
            use_semantic_search = st.checkbox("Semantic search", value=True, help="More accurate but slower")
            enable_caching = st.checkbox("Enable caching", value=True, help="Cache responses for faster repeated queries")

        # System Statistics with Technology Breakdown
        st.subheader("📊 System Statistics")
        try:
            stats = components['vector_store'].get_collection_stats()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Chunks", stats.get('total_chunks', 0))
            with col2:
                st.metric("Technologies", len(TECHNOLOGY_MAPPING))

            # Technology breakdown
            if 'comprehensive_docs' in stats.get('sources', {}):
                st.write("**Available Technologies:**")
                for tech_key, tech_name in TECHNOLOGY_MAPPING.items():
                    st.markdown(f'<div class="tech-badge">{tech_name}</div>', unsafe_allow_html=True)

            # Provider status
            provider_status = enhanced_llm_handler.get_provider_status()
            st.write("**LLM Providers:**")
            for provider, available in provider_status.items():
                status_icon = "✅" if available else "❌"
                st.write(f"{status_icon} {provider.title()}")

        except Exception as e:
            st.error(f"Could not load stats: {e}")

        # Enhanced Chat History
        st.subheader("💬 Recent Queries")
        if 'chat_history' in st.session_state and st.session_state.chat_history:
            for i, msg in enumerate(st.session_state.chat_history[-3:]):  # Show last 3
                mode_icon = "🔧" if msg.get('mode') == 'code' else "📖" if msg.get('mode') == 'detailed' else "💭"
                with st.expander(f"{mode_icon} {msg['question'][:25]}...", expanded=False):
                    st.write(f"**Q:** {msg['question']}")
                    st.write(f"**Mode:** {msg.get('mode', 'normal').title()}")
                    st.write(f"**Sources:** {msg['sources_count']}")
                    st.write(f"**Time:** {msg['response_time']:.2f}s")

            if st.button("Clear History", key="clear_history"):
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.info("No recent queries")

        # Document Upload Section
        st.subheader("📁 Document Upload")

        # Show supported formats
        supported_formats = components['document_processor'].get_supported_formats()
        st.info(f"**Supported formats:** {', '.join(supported_formats)}")

        uploaded_files = st.file_uploader(
            "Upload documents to expand knowledge base",
            type=[fmt.replace('.', '') for fmt in supported_formats],
            accept_multiple_files=True,
            help="Upload files to add to the RAG system"
        )

        if uploaded_files:
            if st.button("Process Uploaded Files", type="primary"):
                with st.spinner("Processing documents..."):
                    processed_count = 0
                    for uploaded_file in uploaded_files:
                        try:
                            # Read file content
                            file_content = uploaded_file.read()

                            # Process document
                            result = components['document_processor'].process_file(uploaded_file.name, file_content)

                            if result['success']:
                                # Create document object
                                document = {
                                    'title': uploaded_file.name,
                                    'content': result['content'],
                                    'source': 'user_upload',
                                    'file_type': uploaded_file.type or 'unknown'
                                }

                                # Chunk the document
                                chunks = components['chunker'].chunk_document(document)

                                if chunks:
                                    texts = [chunk['content'] for chunk in chunks]
                                    metadatas = [chunk['metadata'] for chunk in chunks]
                                    ids = [f"upload_{uploaded_file.name}_{i}" for i in range(len(chunks))]

                                    added = components['vector_store'].add_documents(texts, metadatas, ids)
                                    processed_count += 1

                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {str(e)}")

                    if processed_count > 0:
                        st.success(f"Successfully processed {processed_count} document(s)!")
                        st.rerun()  # Refresh to update stats
                    else:
                        st.error("No documents were processed successfully")

        return {
            'search_k': search_k,
            'enable_web_search': enable_web_search,
            'selected_tech': selected_tech,
            'source_filter': source_filter,
            'technology_filter': technology_filter,
            'response_mode': response_mode,
            'chunk_overlap': chunk_overlap,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'use_semantic_search': use_semantic_search,
            'enable_caching': enable_caching
        }

def generate_enhanced_response(user_input: str, ui_settings: Dict, components: Dict):
    """Generate enhanced response based on mode and settings"""
    start_time = time.time()
    search_results = []

    try:
        # Combine filters for more targeted search
        combined_filter = {}
        if ui_settings['source_filter']:
            combined_filter.update(ui_settings['source_filter'])
        if ui_settings['technology_filter']:
            combined_filter.update(ui_settings['technology_filter'])

        filter_dict = combined_filter if combined_filter else None

        # Enhanced search with overlap
        if ui_settings['response_mode'] != "Web Only":
            search_results = components['vector_store'].search(
                user_input,
                k=ui_settings['search_k'] + ui_settings['chunk_overlap'],
                filter_dict=filter_dict
            )

        # Add web search if enabled
        if ui_settings['enable_web_search']:
            web_results = web_search_provider.search_web(user_input, max_results=3)
            search_results.extend(web_results)

        # Generate response based on mode
        if ui_settings['response_mode'] == "Code Generation":
            # Enhanced code generation with technology context
            tech_context = ""
            if ui_settings['selected_tech'] != "All Technologies":
                tech_name = ui_settings['selected_tech'].replace("📚 ", "").replace("📄 ", "")
                tech_context = f"Focus on {tech_name} implementation. "

            code_prompt = f"{tech_context}Provide a complete, working code implementation for: {user_input}"
            answer = enhanced_llm_handler.generate_code(code_prompt, "python", search_results[:5])

            # Format code response
            if "```" not in answer:
                answer = f"```python\n{answer}\n```"

        elif ui_settings['response_mode'] == "Detailed Sources":
            # Generate answer with detailed source focus
            detailed_prompt = f"Provide a comprehensive answer with specific references to documentation. Question: {user_input}"
            answer = enhanced_llm_handler.generate_answer(detailed_prompt, search_results)

        else:  # Smart Answer
            # Enhanced smart answer
            smart_prompt = f"Provide a clear, practical answer. Use examples when helpful. Question: {user_input}"
            answer = enhanced_llm_handler.generate_answer(smart_prompt, search_results)

        response_time = time.time() - start_time

        return {
            'answer': answer,
            'sources': search_results,
            'response_time': response_time,
            'mode': ui_settings['response_mode'].lower().replace(' ', '_')
        }

    except Exception as e:
        return {
            'answer': f"Error generating response: {str(e)}",
            'sources': [],
            'response_time': time.time() - start_time,
            'mode': 'error'
        }

def generate_web_only_response(user_input: str, ui_settings: Dict, components: Dict):
    """Generate response using web search only"""
    start_time = time.time()

    try:
        # Get web search results only
        web_results = components['web_search_provider'].search_web(user_input, max_results=5)

        if not web_results:
            return {
                'answer': "No web search results found for your query. Please try a different search term.",
                'sources': [],
                'response_time': time.time() - start_time,
                'mode': 'web_only'
            }

        # Generate answer based on web results only
        answer = components['enhanced_llm_handler'].generate_answer(
            f"Based on web search results, answer this question: {user_input}",
            web_results
        )

        return {
            'answer': answer,
            'sources': web_results,
            'response_time': time.time() - start_time,
            'mode': 'web_only'
        }

    except Exception as e:
        return {
            'answer': f"Web search error: {str(e)}",
            'sources': [],
            'response_time': time.time() - start_time,
            'mode': 'error'
        }

def render_enhanced_sources(sources: List[Dict], mode: str):
    """Render enhanced source display based on mode"""
    if not sources:
        return

    if mode == "detailed_sources":
        st.subheader("📖 Detailed Sources")
        for i, source in enumerate(sources[:8]):  # Show more sources in detailed mode
            with st.expander(f"📄 Source {i+1}: {source.get('metadata', {}).get('title', 'Unknown')}", expanded=False):
                metadata = source.get('metadata', {})

                st.markdown(f"**Technology:** {metadata.get('technology', 'Unknown').title()}")
                st.markdown(f"**Source:** {metadata.get('source', 'Unknown')}")
                if metadata.get('page'):
                    st.markdown(f"**Page:** {metadata.get('page')}")

                content = source.get('content', '')
                if len(content) > 500:
                    st.markdown(f"**Content Preview:**\n{content[:500]}...")
                    with st.expander("Show full content"):
                        st.text(content)
                else:
                    st.markdown(f"**Content:**\n{content}")

    else:
        # Compact source display
        if sources:
            st.subheader(f"📚 Sources ({len(sources)})")

            # Group sources by technology and web search
            tech_groups = {}
            web_results = []

            for source in sources[:6]:
                metadata = source.get('metadata', {})

                # Check if this is a web search result
                if metadata.get('source') == 'web_search':
                    web_results.append(source)
                else:
                    tech = metadata.get('technology', 'other')
                    if tech not in tech_groups:
                        tech_groups[tech] = []
                    tech_groups[tech].append(source)

            # Display web search results first with special formatting
            if web_results:
                st.markdown("**🌐 Web Search Results:**")
                for i, source in enumerate(web_results):
                    metadata = source.get('metadata', {})
                    provider = metadata.get('provider', 'web').replace('_', ' ').title()
                    title = metadata.get('title', 'Web Result')
                    url = metadata.get('url', '')

                    if url:
                        st.markdown(f"• **[{title}]({url})** *(via {provider})*")
                    else:
                        st.markdown(f"• **{title}** *(via {provider})*")

                    content = source.get('content', '')[:150] + "..." if len(source.get('content', '')) > 150 else source.get('content', '')
                    st.markdown(f"  {content}")
                st.markdown("---")

            # Display local documentation results
            for tech, tech_sources in tech_groups.items():
                tech_name = TECHNOLOGY_MAPPING.get(tech, tech.title())
                st.markdown(f"**{tech_name}:** {len(tech_sources)} references")

def render_main_interface(components: Dict, ui_settings: Dict):
    """Render the main chat interface"""
    st.markdown('<h1 class="main-header">📚 DocuMentor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Documentation Assistant with Smart Search & Code Generation</p>', unsafe_allow_html=True)

    # Mode indicator
    mode_class = f"mode-{ui_settings['response_mode'].lower().replace(' ', '')}"
    st.markdown(f'<div class="response-mode-indicator {mode_class}">Mode: {ui_settings["response_mode"]}</div>', unsafe_allow_html=True)

    # Enhanced input interface with modern design
    with st.container():
        # Input section with improved layout
        user_input = st.text_input(
            "💬 Ask anything about your documents:",
            placeholder=f"e.g., How do I implement authentication in {ui_settings['selected_tech'].replace('📚 ', '').replace('📄 ', '')}? Or ask about any technology...",
            key="user_input",
            help="Type your question here. The AI will search through documentation and provide comprehensive answers."
        )

        # Enhanced button layout
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            if ui_settings['response_mode'] == "Code Generation":
                ask_button = st.button("🔧 Generate Code", type="primary", use_container_width=True)
            elif ui_settings['response_mode'] == "Detailed Sources":
                ask_button = st.button("📖 Deep Research", type="primary", use_container_width=True)
            else:
                ask_button = st.button("🧠 Smart Answer", type="primary", use_container_width=True)

        with col2:
            web_button = st.button("🌍 Web Search", help="Search web only for real-time information", use_container_width=True)

        with col3:
            clear_button = st.button("🗑️ Clear Chat", help="Clear conversation history", use_container_width=True)

        with col4:
            if st.button("📊", help="Show statistics", use_container_width=True):
                st.session_state.show_stats = not st.session_state.get('show_stats', False)

        # Handle clear button
        if clear_button:
            st.session_state.messages = []
            st.rerun()

    # Process input with enhanced feedback
    if (ask_button or web_button) and user_input:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp,
            "mode": ui_settings['response_mode']
        })

        # Generate response
        # Override web search settings if web button was clicked
        if web_button:
            # Force web search only
            modified_settings = ui_settings.copy()
            modified_settings['enable_web_search'] = True
            spinner_text = "Searching web..."
        else:
            modified_settings = ui_settings
            spinner_text = f"Generating {ui_settings['response_mode'].lower()}..."

        with st.spinner(spinner_text):
            if web_button:
                # Web-only search response
                response_data = generate_web_only_response(user_input, modified_settings, components)
            else:
                response_data = generate_enhanced_response(user_input, modified_settings, components)

            # Add assistant response
            assistant_message = {
                "role": "assistant",
                "content": response_data['answer'],
                "sources": response_data['sources'],
                "response_time": response_data['response_time'],
                "timestamp": timestamp,
                "mode": response_data['mode']
            }

            st.session_state.messages.append(assistant_message)

            # Add to chat history
            st.session_state.chat_history.append({
                'question': user_input,
                'answer': response_data['answer'],
                'timestamp': timestamp,
                'sources_count': len(response_data['sources']),
                'response_time': response_data['response_time'],
                'mode': response_data['mode']
            })

        st.rerun()

    # Display enhanced conversation
    if st.session_state.messages:
        st.subheader("💬 Conversation")

        for message in st.session_state.messages:
            if message["role"] == "user":
                mode_icon = "🔧" if message.get("mode") == "Code Generation" else "📖" if message.get("mode") == "Detailed Sources" else "💭"
                with st.chat_message("user"):
                    st.write(f"{mode_icon} {message['content']}")
            else:
                with st.chat_message("assistant"):
                    # Enhanced response display
                    if message.get("mode") == "code_generation":
                        st.markdown("### 🔧 Generated Code:")
                        if "```" in message["content"]:
                            st.markdown(message["content"])
                        else:
                            st.code(message["content"], language="python")
                    else:
                        st.markdown(message["content"])

                    # Performance metrics
                    if "response_time" in message:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Response Time", f"{message['response_time']:.2f}s")
                        with col2:
                            st.metric("Sources Found", len(message.get('sources', [])))
                        with col3:
                            tech_filter = ui_settings['selected_tech'].replace('📚 ', '').replace('📄 ', '')
                            st.metric("Technology", tech_filter if tech_filter != "All Technologies" else "Mixed")

                    # Enhanced source display
                    if message.get('sources'):
                        render_enhanced_sources(message['sources'], message.get('mode', 'normal'))

def main():
    """Main application function"""
    configure_page()

    # Initialize system
    components = initialize_enhanced_rag_system()

    if components['status'] != 'success':
        st.error(f"Failed to initialize system: {components.get('error', 'Unknown error')}")
        return


    # Render sidebar and get settings
    ui_settings = render_enhanced_sidebar(components)

    if not ui_settings:
        return

    # Render main interface
    render_main_interface(components, ui_settings)

if __name__ == "__main__":
    main()