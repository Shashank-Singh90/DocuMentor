import streamlit as st
import requests
import time

st.set_page_config(
    page_title="DocuMentor - AI Documentation Assistant",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (matching original)
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
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ?? Document Type")
    doc_type = st.selectbox("", ["All", "Tutorial", "API Reference", "Conceptual"], index=0)
    
    st.markdown("### ?? Knowledge Base Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Chunks", "0")
    with col2:
        st.metric("Sources", "0")
    
    st.markdown("### ?? Upload Your Documents")
    uploaded_file = st.file_uploader("Upload Markdown, CSV, or Text Files", type=['md', 'csv', 'txt'])
    
    st.markdown("### ?? AI Model Status")
    try:
        response = requests.get("http://localhost:8500/health", timeout=5)
        if response.status_code == 200:
            st.success("? Gemma 3 Ready")
        else:
            st.error("? API Error")
    except:
        st.error("? Ollama not running")
    
    st.markdown("### ?? Try These Questions")
    sample_questions = [
        "What is FastAPI?",
        "How to create a Django model?", 
        "React hooks explained",
        "Docker containerization basics"
    ]
    for question in sample_questions:
        if st.button(question, key=f"sample_{hash(question)}"):
            st.session_state.sample_question = question

# Main content
st.markdown('<h1 class="main-header">?? DocuMentor</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your AI-Powered Documentation Assistant for LangChain & FastAPI</p>', unsafe_allow_html=True)

# Check for sample question
user_input = st.session_state.get('sample_question', '')
if user_input:
    del st.session_state.sample_question

st.markdown("### ?? Ask DocuMentor Anything")
query = st.text_input(
    "Ask about LangChain or FastAPI:",
    value=user_input,
    placeholder="e.g., How do I create a FastAPI application with authentication?",
)

col1, col2, col3 = st.columns(3)
with col1:
    ask_button = st.button("?? Ask DocuMentor")
with col2:
    st.button("??? Clear Chat")
with col3:
    st.button("?? Random Example")

st.markdown("### ?? Conversation")

if ask_button and query:
    st.markdown(f"**You:** {query}")
    with st.spinner("?? Gemma 3 is thinking..."):
        try:
            response = requests.post(
                "http://localhost:8500/ask",
                json={"question": query},
                timeout=300
            )
            if response.status_code == 200:
                data = response.json()
                st.markdown("**DocuMentor:**")
                st.write(data.get('answer', 'No response'))
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Response Time", f"{data.get('response_time', 0):.2f}s")
                with col2:
                    st.metric("Confidence", "85%")
                with col3:
                    st.metric("Sources Found", len(data.get('sources', [])))
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    ?? <strong>DocuMentor</strong> - AI-Powered Documentation Assistant<br>
    <small>Built with Python, Streamlit, and Gemma 3</small>
</div>
""", unsafe_allow_html=True)





