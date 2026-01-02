import streamlit as st
import requests
import base64
import time
import io
import os
import json
from PIL import Image

st.set_page_config(page_title="Motion Studio", layout="wide")

# --- SIDEBAR: SYSTEM SETTINGS ---
with st.sidebar:
    st.title("⚙️ Production Settings")
    quality_setting = st.selectbox("Render Quality", ["720p", "1080p"], index=0)
    st.divider()
    st.info("Archive Tip: Use 720p for faster iterations.")

st.title("🎬 Uncensored Motion Studio")

# 1. AUTHENTICATION CHECK
if 'AI_API_KEY' not in st.secrets:
    st.error("Missing AI_API_KEY in Streamlit Secrets!")
    st.stop()

api_key = st.secrets["AI_API_KEY"]
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 2. IMAGE INGESTION
uploaded_file = st.file_uploader("Upload Image to Animate", type=["jpg", "png", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        img = Image.open(uploaded_file)
        st.image(img, caption="Source Reference", use_container_width=True)
    
    with col2:
        motion_prompt = st.text_area("Motion Description:", 
                                     placeholder="e.g., Cinematic slow motion, hair blowing in the wind, violet light flickering...",
                                     height=150)
        generate_btn = st.button("🚀 Generate Motion")

    if generate_btn:
        if not motion_prompt:
            st.warning("The archive requires a prompt to generate motion.")
            st.stop()

        with st.status("Waking the machine...", expanded=True) as status:
            try:
                # STEP A: UPLOAD TO KIE CLOUD
                st.write("Encoding pixel data...")
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=90)
                b64_str = base64.b64encode(buffered.getvalue()).decode()
                
                upload_payload = {
                    "base64Data": f"data:image/jpeg;base64,{b64_str}",
                    "uploadPath": "images/temp",
                    "fileName": f"gen_{int(time.time())}.jpg"
                }
                
                up_res = requests.post("https://api.kie.ai/api/file-base64-upload", 
                                       json=upload_payload, headers=headers).json()
                
                if not up_res.get("success"):
                    st.error(f"Upload Failed: {up_res.get('msg')}")
                    st.stop()

                temp_url = up_res["data"]["downloadUrl"]
                st.write("Image anchored. Initializing Gen-3 Turbo...")

                # STEP B: TRIGGER GENERATION
                gen_payload = {
                    "prompt": motion_prompt,
                    "imageUrl": temp_url,
                    "model": "runway-gen3-alpha-turbo",
                    "duration": 5,
                    "quality": quality_setting,
                    "aspectRatio": "16:9"
                }
                
                gen_res = requests.post("https://api.kie.ai/api/v1/runway/generate", 
                                        json=gen_payload, headers=headers).json()
                
                if gen_res.get("code") != 200:
                    st.error(f"Generation Error: {gen_res.get('msg')}")
                    st.stop()

                task_id = gen_res["data"]["taskId"]
                st.write(f"Task Logged: {task_id}. Analyzing frames...")

                # STEP C: POLLING FOR COMPLETION
                video_url = None
                progress_bar = st.progress(0)
                
                for i in range(40): # 200 seconds max
                    time.sleep(5)
                    progress_bar.progress((i + 1) / 40)
                    
                    check_res = requests.get(f"https://api.kie.ai/api/v1/runway/record-info?taskId={task_id}", 
                                             headers=headers).json()
                    
                    # Kie AI success logic
                    if check_res.get("data", {}).get("successFlag") == 1:
                        results = check_res["data"].get("resultUrls")
                        # Handle if resultUrls is a string or a list
                        video_url = json.loads(results)[0] if isinstance(results, str) else results[0]
                        break
                    elif check_res.get("data", {}).get("successFlag") == 2:
                        st.error("Generation Failed in the cloud.")
                        st.stop()

                if video_url:
                    status.update(label="Motion Captured!", state="complete", expanded=False)
                    st.video(video_url)
                    
                    # ARCHIVE TO GALLERY
                    os.makedirs("gallery", exist_ok=True)
                    v_data = requests.get(video_url).content
                    save_path = f"gallery/v_{task_id}.mp4"
                    with open(save_path, "wb") as f:
                        f.write(v_data)
                    st.success(f"Video archived to {save_path}")
                    st.download_button("💾 Download Master", v_data, file_name=f"motion_{task_id}.mp4")
                else:
                    st.error("Render Timed Out. The system is still processing in the background.")

            except Exception as e:
                st.error(f"Forensic Alert: {str(e)}")
