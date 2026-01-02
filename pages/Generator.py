import streamlit as st
import requests
import base64
import time
import io
import os
import json
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Motion Studio | Command Center", layout="wide")

# Custom CSS for that 'Violet Noir' aesthetic
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { background-color: #4b0082; color: white; border-radius: 5px; }
    .stTextArea>div>div>textarea { background-color: #1a1c23; color: #bb86fc; }
    </style>
    """, unsafe_allow_stdio=True)

# --- SIDEBAR: SYSTEM SETTINGS ---
with st.sidebar:
    st.title("⚙️ System Admin")
    quality_setting = st.selectbox("Render Quality", ["720p", "1080p"], index=0)
    st.divider()
    if st.button("🗑️ Clear Local Archive"):
        if os.path.exists("gallery"):
            import shutil
            shutil.rmtree("gallery")
            st.success("Archive Purged.")

st.title("🎬 Uncensored Motion Studio")
st.caption("Year Zero // Project Violet // Forensic Motion Engine")

# 1. AUTHENTICATION
if 'AI_API_KEY' not in st.secrets:
    st.error("Missing AI_API_KEY in Streamlit Secrets!")
    st.stop()

api_key = st.secrets["AI_API_KEY"]
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 2. FILE INGESTION
uploaded_file = st.file_uploader("Upload Image to Animate", type=["jpg", "png", "jpeg"])

if uploaded_file:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        img = Image.open(uploaded_file)
        # Forensic Resize: Prevents "Connection Empty" by ensuring payload isn't too massive
        if img.width > 1280 or img.height > 1280:
            img.thumbnail((1280, 1280))
        st.image(img, caption="Source Reference (Optimized)", use_container_width=True)
    
    with col2:
        motion_prompt = st.text_area("Motion Description:", 
                                     placeholder="e.g., Violet lightning flickers, cinematic slow motion, wind through hair...",
                                     height=180)
        generate_btn = st.button("🚀 Deploy Motion Engine")

    if generate_btn:
        if not motion_prompt:
            st.warning("The archive requires a prompt to generate motion.")
            st.stop()

        with st.status("Initializing Handshake...", expanded=True) as status:
            try:
                # --- STEP A: UPLOAD TO KIE CLOUD ---
                st.write("🔒 Securing pixel tunnel...")
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85) 
                img_bytes = buffered.getvalue()
                b64_str = base64.b64encode(img_bytes).decode('utf-8')
                
                upload_payload = {
                    "base64Data": f"data:image/jpeg;base64,{b64_str}",
                    "uploadPath": "images/temp",
                    "fileName": f"gen_{int(time.time())}.jpg"
                }
                
                up_res_raw = requests.post("https://api.kie.ai/api/file-base64-upload", 
                                          json=upload_payload, headers=headers, timeout=45)
                up_res = up_res_raw.json()
                
                if not up_res.get("success"):
                    st.error(f"Kie Rejection: {up_res.get('msg')}")
                    st.stop()

                temp_url = up_res["data"]["downloadUrl"]
                st.write("✅ Image anchored. Calling Gen-3 Turbo...")

                # --- STEP B: TRIGGER GENERATION ---
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
                    st.error(f"Engine Error: {gen_res.get('msg')}")
                    st.stop()

                task_id = gen_res["data"]["taskId"]
                st.write(f"📂 Task Logged: {task_id}. Rendering pixels...")

                # --- STEP C: POLLING ---
                video_url = None
                progress_bar = st.progress(0)
                
                for i in range(50): # 250 seconds max
                    time.sleep(5)
                    progress_bar.progress((i + 1) / 50)
                    
                    check_res = requests.get(f"https://api.kie.ai/api/v1/runway/record-info?taskId={task_id}", 
                                             headers=headers).json()
                    
                    data = check_res.get("data", {})
                    if data.get("successFlag") == 1:
                        results = data.get("resultUrls")
                        # Fix for string vs list format in resultUrls
                        video_url = json.loads(results)[0] if isinstance(results, str) else results[0]
                        break
                    elif data.get("successFlag") == 2:
                        st.error("The cloud failed to render this coordinate.")
                        st.stop()

                if video_url:
                    status.update(label="Capture Complete.", state="complete", expanded=False)
                    st.video(video_url)
                    
                    # --- LOCAL ARCHIVING ---
                    os.makedirs("gallery", exist_ok=True)
                    v_data = requests.get(video_url).content
                    save_path = f"gallery/v_{task_id}.mp4"
                    with open(save_path, "wb") as f:
                        f.write(v_data)
                    
                    st.success("Video committed to local archive.")
                    st.download_button("💾 Download Master File", v_data, file_name=f"violet_motion_{task_id}.mp4")
                else:
                    st.error("The gaze timed out. Check the task later.")

            except Exception as e:
                st.error(f"System Glitch: {str(e)}")
