import streamlit as st
import requests
import time

st.set_page_config(
    page_title="DocuMentor - AI Documentation Assistant",
    page_icon="🧠",
    layout="wide"
)

st.markdown('<h1 style="text-align: center; color: #42A5F5;">🧠 DocuMentor</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Your AI-Powered Documentation Assistant with Gemma 3</p>', unsafe_allow_html=True)

# Check API status
try:
    response = requests.get("http://localhost:8000/stats", timeout=5)
    if response.status_code == 200:
        st.success("✅ API Server Connected - Gemma 3 Ready")
    else:
        st.error("❌ API Server Error")
except:
    st.error("❌ API Server Not Connected - Start with: python api_server.py")

# Chat interface
query = st.text_input("Ask about any technology:", placeholder="e.g., What is FastAPI?")

if st.button("Ask DocuMentor") and query:
    with st.spinner("🤖 Gemma 3 is thinking..."):
        try:
            response = requests.post(
                "http://localhost:8000/ask",
                json={"question": query},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                st.write("**DocuMentor:**")
                st.write(data.get('answer', 'No response'))
                
                # Show response time
                if 'response_time' in data:
                    st.caption(f"Response time: {data['response_time']:.2f}s")
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
