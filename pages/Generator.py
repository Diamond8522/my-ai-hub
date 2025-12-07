import streamlit as st
import requests
import base64
import time
import io
import os
from PIL import Image

st.set_page_config(page_title="Motion Studio", layout="wide")

# --- SIDEBAR OPTIONS ---
st.sidebar.title("⚙️ Production Settings")
quality_setting = st.sidebar.selectbox("Render Quality", ["720p", "1080p"], index=0)
st.sidebar.divider()
st.sidebar.info("Grit Tip: Start with 720p to save trial credits.")

st.title("🎬 Uncensored Motion Studio")

# 1. API Check
if 'AI_API_KEY' not in st.secrets:
    st.error("Missing API Key in Secrets!")
    st.stop()

# 2. Upload Spot (Improved handling)
uploaded_file = st.file_uploader("Upload Image to Animate", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Reference", width=300)
    
    motion_prompt = st.text_area("Motion Description:", placeholder="e.g., Lightning flickers, kinetic motion...")

    if st.button("Generate Video"):
        with st.spinner("Processing Pixel Data..."):
            try:
                api_key = st.secrets["AI_API_KEY"]
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                
                # Encode Image properly for Kie temp storage
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                b64_str = base64.b64encode(buffered.getvalue()).decode()
                
                upload_payload = {
                    "base64Data": f"data:image/jpeg;base64,{b64_str}",
                    "uploadPath": "images/temp",
                    "fileName": f"temp_{int(time.time())}.jpg"
                }
                
                up_res = requests.post("https://api.kie.ai/api/file-base64-upload", json=upload_payload, headers=headers).json()
                
                if up_res.get("success") and "downloadUrl" in up_res.get("data", {}):
                    temp_url = up_res["data"]["downloadUrl"]
                    
                    gen_payload = {
                        "prompt": motion_prompt,
                        "imageUrl": temp_url,
                        "model": "runway-gen3-alpha-turbo",
                        "duration": 5,
                        "quality": quality_setting, # Pulled from Sidebar Option
                        "aspectRatio": "16:9"
                    }
                    
                    gen_res = requests.post("https://api.kie.ai/api/v1/runway/generate", json=gen_payload, headers=headers).json()
                    
                    if gen_res.get("code") == 200:
                        task_id = gen_res["data"]["taskId"]
                        st.info(f"Task Started (ID: {task_id}). Rendering...")
                        
                        # --- POLLING ---
                        for _ in range(30):
                            time.sleep(5)
                            status = requests.get(f"https://api.kie.ai/api/v1/runway/record-info?taskId={task_id}", headers=headers).json()
                            if status["data"]["successFlag"] == 1:
                                video_url = eval(status["data"]["resultUrls"])[0]
                                st.video(video_url)
                                # Local Archive
                                if not os.path.exists("gallery"): os.makedirs("gallery")
                                v_data = requests.get(video_url).content
                                with open(f"gallery/v_{task_id}.mp4", "wb") as f: f.write(v_data)
                                st.success("Created! Archived in Gallery.")
                                break
                    else:
                        st.error(f"Kie Rejection: {gen_res.get('msg')}")
                else:
                    st.error(f"Kie.ai Upload failed: {up_res.get('msg', 'Connection empty')}")
            except Exception as e:
                st.error(f"System Glitch: {e}")
