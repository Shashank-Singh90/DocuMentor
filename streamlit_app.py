import streamlit as st
import requests
import pandas as pd
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

# Streamlit configuration
st.set_page_config(
    page_title="DocuMentor - AI Documentation Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for cloud deployment
st.markdown("""
<style>
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
    
    .user-message {
        background-color: #E3F2FD;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        margin-left: 10%;
        color: #333333;
        border: 1px solid #90CAF9;
    }
    
    .assistant-message {
        background-color: #F5F5F5;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        margin-right: 10%;
        color: #333333;
        border: 1px solid #E0E0E0;
    }
    
    .stButton > button {
        background-color: #42A5F5;
        color: white !important;
        border-radius: 0.5rem;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
        transition: background-color 0.3s;
        box-shadow: 0 2px 4px rgba(66, 165, 245, 0.3);
    }
    
    .stButton > button:hover {
        background-color: #1976D2;
        box-shadow: 0 4px 8px rgba(66, 165, 245, 0.4);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_demo_system():
    """Initialize a demo version for cloud deployment"""
    try:
        # For cloud deployment, we'll use a simplified demo
        return {
            'status': 'demo',
            'message': 'Running in demo mode for cloud deployment'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def demo_search_and_respond(query: str) -> dict:
    """Demo search function for cloud deployment"""
    # This is a simplified demo response
    demo_responses = {
        "fastapi": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. Key features include automatic API documentation, data validation, and high performance.",
        "django": "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It follows the model-template-views architectural pattern.",
        "react": "React is a JavaScript library for building user interfaces, particularly web applications. It allows developers to create reusable UI components and manage application state efficiently.",
        "python": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used for web development, data science, automation, and more.",
        "docker": "Docker is a platform that enables developers to package applications into containers—standardized executable components combining application source code with the OS libraries and dependencies required to run that code.",
        "default": "I'm running in demo mode! In the full version, I have access to 13,606+ documentation chunks covering LangChain, FastAPI, Django, React, Python, Docker, PostgreSQL, MongoDB, and TypeScript."
    }
    
    query_lower = query.lower()
    for key, response in demo_responses.items():
        if key in query_lower:
            return {
                'answer': response,
                'sources': [{'title': f'{key.title()} Documentation', 'source': key}],
                'response_time': 0.1,
                'confidence': 0.85
            }
    
    return {
        'answer': demo_responses['default'],
        'sources': [{'title': 'Demo Mode', 'source': 'demo'}],
        'response_time': 0.1,
        'confidence': 0.5
    }

def main():
    """Main application for cloud deployment"""
    # Header
    st.markdown('<h1 class="main-header">🧠 DocuMentor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Documentation Assistant</p>', unsafe_allow_html=True)
    
    # Initialize demo system
    components = initialize_demo_system()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Demo Information")
        
        st.info("""
        🎯 **Welcome to DocuMentor Demo!**
        
        This is a cloud-deployed demo version of DocuMentor.
        
        **Features:**
        - 🧠 AI-powered responses
        - 📚 Multi-technology knowledge
        - 🔍 Intelligent search
        - 📊 Source citations
        
        **Supported Topics:**
        - Python, FastAPI, Django
        - React, TypeScript, Next.js
        - Docker, PostgreSQL, MongoDB
        - LangChain, and more!
        """)
        
        st.subheader("💡 Try These Questions")
        sample_questions = [
            "What is FastAPI?",
            "How to create a Django model?",
            "React hooks explained",
            "Docker containerization basics",
            "Python list comprehensions"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{hash(question)}"):
                st.session_state.sample_question = question
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Check for sample question
    if 'sample_question' in st.session_state:
        user_input = st.session_state.sample_question
        del st.session_state.sample_question
    else:
        user_input = None
    
    # Main interface
    st.subheader("💬 Ask DocuMentor Anything")
    
    # Chat input
    query = st.text_input(
        "Ask about any technology:",
        value=user_input if user_input else "",
        placeholder="e.g., How to build a FastAPI application with authentication?",
        key="chat_input"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ask_button = st.button("🚀 Ask DocuMentor", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear Chat", use_container_width=True)
    
    # Handle buttons
    if clear_button:
        st.session_state.messages = []
        st.rerun()
    
    if ask_button and query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Generate demo response
        with st.spinner("🤔 Thinking..."):
            response = demo_search_and_respond(query)
        
        # Add assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response['answer'],
            "sources": response['sources'],
            "response_time": response['response_time'],
            "confidence": response['confidence']
        })
    
    # Display chat
    if st.session_state.messages:
        st.subheader("📚 Conversation")
        
        for message in st.session_state.messages:
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
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # Show metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Response Time", f"{message['response_time']:.2f}s")
                with col2:
                    st.metric("Confidence", f"{message['confidence']:.0%}")
                with col3:
                    st.metric("Sources", len(message.get('sources', [])))
                
                st.markdown("---")
    else:
        # Welcome message
        st.info("""
        👋 **Welcome to DocuMentor Demo!**
        
        I'm your AI assistant for development documentation. Try asking about:
        
        • **Web Frameworks** - Django, FastAPI, React, Next.js
        • **Programming** - Python, TypeScript, JavaScript
        • **DevOps** - Docker, PostgreSQL, MongoDB
        • **AI/ML** - LangChain, machine learning concepts
        
        Ask a question above or click the sample questions in the sidebar! 🚀
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🧠 <strong>DocuMentor Demo</strong> - AI-Powered Documentation Assistant<br>
        <small>Built with Python, Streamlit, and advanced AI technologies</small><br>
        <small>⭐ <a href="https://github.com/Shashank-Singh90/DocuMentor" target="_blank">Star on GitHub</a> | 🌐 Full version available with 13,606+ documentation chunks</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()