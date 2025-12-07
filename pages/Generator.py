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
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Source", width=300)
    
    # 4. Motion Prompt for the AI
    motion_prompt = st.text_area("How should it move?", 
                                placeholder="Pan left slowly, cinematic lighting, hair swaying...")

    if st.button("Generate Unrestricted Video"):
        with st.spinner("Pushing to Kie.ai... rendering motion..."):
            try:
                # --- START OF Risky Code ---
                api_key = st.secrets["AI_API_KEY"]
                api_url = "https://api.kie.ai/api/v1/runway/generate"
                
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "prompt": motion_prompt,
                    "imageUrl": f"data:image/jpeg;base64,{img_b64}",
                    "model": "runway-gen3-alpha-turbo",
                    "duration": 5,
                    "aspectRatio": "16:9"
                }

                # Submit task
                submit_res = requests.post(api_url, json=payload, headers=headers).json()
                
                if submit_res.get("code") == 200:
                    task_id = submit_res["data"]["taskId"]
                    st.info(f"Task ID: {task_id}. Animating pixels...")
                    
                    status_url = f"https://api.kie.ai/api/v1/runway/record-info?taskId={task_id}"
                    for i in range(24):
                        time.sleep(5)
                        res = requests.get(status_url, headers=headers).json()
                        
                        if res["data"]["successFlag"] == 1:
                            final_urls = eval(res["data"]["resultUrls"])
                            video_url = final_urls[0]
                            st.video(video_url)
                            st.success("Generation Complete!")
                            
                            # Save result
                            video_data = requests.get(video_url).content
                            save_path = f"gallery/video_{task_id}.mp4"
                            with open(save_path, "wb") as f:
                                f.write(video_data)
                            st.info(f"Video archived in hub: {save_path}")
                            break
                        elif res["data"]["successFlag"] >= 2:
                            st.error(f"Kie.ai Error: {res.get('msg')}")
                            break
                else:
                    st.error(f"Kie.ai reject: {submit_res.get('msg')}")

            # --- THE SAFETY NET: Closing the Try Block ---
            except Exception as e:
                st.error(f"Network or system glitch: {e}")
            finally:
                # This always runs to clear memory
                buffered.close()
