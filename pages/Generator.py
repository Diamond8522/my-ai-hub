import streamlit as st
import requests
import base64
import time
import io
import os
from PIL import Image

st.set_page_config(page_title="Grit Motion Studio", layout="wide")
st.title("🎬 Uncensored Motion Studio")

# 1. API Secret Verification
if 'AI_API_KEY' not in st.secrets:
    st.error("Grit needed: Add 'AI_API_KEY' to your Streamlit Secrets dashboard!")
    st.stop()

# 2. Setup Gallery Folder locally
if not os.path.exists("gallery"):
    os.makedirs("gallery")

# 3. User Upload Spot
uploaded_file = st.file_uploader("Upload Image to Animate", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Display preview image
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Source", width=300)
    
    # 4. Motion Prompt for the AI
    motion_prompt = st.text_area("How should it move?", 
                                placeholder="Pan left slowly, cinematic lighting, hair swaying...")

    if st.button("Generate Unrestricted Video"):
        with st.spinner("Pushing to Kie.ai... rendering motion..."):
            try:
                # Auth
                api_key = st.secrets["AI_API_KEY"]
                api_url = "https://api.kie.ai/api/v1/runway/generate"
                
                # Convert Image to Base64 data string
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()

                headers
