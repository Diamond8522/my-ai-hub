import streamlit as st
import requests
import base64
import os
import time
import io
from PIL import Image

# 1. Dashboard UI setup
st.set_page_config(page_title="Motion Studio", layout="wide")
st.title("🎬 Uncensored Motion Studio")
st.write("Turn your static images into unrestricted cinematic video.")

# 2. File Uploader Spot
uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Display preview
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Source", width=400)
    
    # Motion Prompt
    prompt = st.text_area("Describe how this photo moves:", 
                          placeholder="e.g., slow motion zoom, cinematic lighting flicker...")

    if st.button("Generate Unrestricted Video"):
        if not prompt:
            st.error("Please provide a motion description.")
        else:
            with st.spinner("Bypassing filters... animating pixels..."):
                try:
                    # ACCESS KEY: Ensure 'AI_API_KEY' is in your Streamlit Secrets!
                    api_key = st.secrets["AI_API_KEY"]
                    
                    # NOVITA API ENDPOINT (Wan 2.1 Image-to-Video)
                    # This model allows the unmoderated 'enable_safety_checker=False' flag
                    api_url = "https://api.novita.ai/v3/async/wan-i2v"
                    
                    # Convert image to Base64 (Standard for AI data transfer)
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    img_b64 = base64.b64encode(buffered.getvalue()).decode()

                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "prompt": prompt,
                        "image_url": f"data:image/jpeg;base64,{img_b64}",
                        "enable_safety_checker": False # THE GRIT SWITCH: UNRESTRICTED
                    }

                    # Step 1: Submit Task
                    response = requests.post(api_url, json=payload, headers=headers)
                    task_data = response.json()
                    
                    if "task_id" in task_data:
                        task_id = task_data["task_id"]
                        
                        # Step 2: Poll for results (Simplified)
                        # In production, use a loop to check status. Here we wait once for demo.
                        time.sleep(10) 
                        result_url = f"https://api.novita.ai/v3/async/task-result?task_id={task_id}"
                        res = requests.get(result_url, headers=headers).json()
                        
                        if res['task']['status'] == "TASK_STATUS_SUCCEED":
                            video_url = res['videos'][0]['video_url']
                            
                            # SHOW VIDEO
                            st.video(video_url)
                            
                            # SAVE TO GALLERY FOLDER
                            if not os.path.exists("gallery"): os.makedirs("gallery")
                            v_data = requests.get(video_url).content
                            f_path = f"gallery/video_{int(time.time())}.mp4"
                            with open(f_path, "wb") as f:
                                f.write(v_data)
                            st.success(f"Video saved to hub: {f_path}")
                        else:
                            st.warning("Video is still cooking in the oven... check back in a minute!")
                    else:
                        st.error(f"API Error: {task_data}")

                except Exception as e:
                    st.error(f"Scary glitch detected: {e}")
