import streamlit as st
import requests
import base64
import time
import io
import os
from PIL import Image

st.set_page_config(page_title="Grit Motion Studio", layout="wide")
st.title("🎬 Uncensored Motion Studio")

# 1. Secret Check
if 'AI_API_KEY' not in st.secrets:
    st.error("Add 'AI_API_KEY' to your Secrets first!")
    st.stop()

# 2. Setup
if not os.path.exists("gallery"): os.makedirs("gallery")

# 3. Spot to Upload
uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Source", width=300)
    
    motion_prompt = st.text_area("How should it move?", placeholder="Cinematic slow pan...")

    if st.button("Generate Video"):
        with st.spinner("Pushing to Kie engine... bypassing filters..."):
            try:
                api_key = st.secrets["AI_API_KEY"]
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                
                # Encode & Upload to temp storage (Fixes 'illegal' error)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=80)
                b64_str = base64.b64encode(buffered.getvalue()).decode()
                
                upload_payload = {
                    "base64Data": f"data:image/jpeg;base64,{b64_str}",
                    "uploadPath": "images/temp",
                    "fileName": f"temp_{int(time.time())}.jpg"
                }
                
                up_res = requests.post("https://api.kie.ai/api/file-base64-upload", json=upload_payload, headers=headers).json()
                
                if up_res.get("success"):
                    temp_image_url = up_res["data"]["downloadUrl"]

                    # FINAL FIX: Add 'quality' parameter
                    gen_payload = {
                        "prompt": motion_prompt,
                        "imageUrl": temp_image_url,
                        "model": "runway-gen3-alpha-turbo",
                        "duration": 5,
                        "quality": "720p", # THIS IS THE FIX
                        "aspectRatio": "16:9"
                    }
                    
                    gen_res = requests.post("https://api.kie.ai/api/v1/runway/generate", json=gen_payload, headers=headers).json()
                    
                    if gen_res.get("code") == 200:
                        task_id = gen_res["data"]["taskId"]
                        st.info("Generation task live...")
                        # Polling logic...
                    else:
                        st.error(f"Gen Reject: {gen_res.get('msg')}")
                else:
                    st.error(f"Upload Error: {up_res.get('msg')}")

            except Exception as e:
                st.error(f"Glitch detected: {e}")
