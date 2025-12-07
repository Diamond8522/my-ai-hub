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
    st.error("Grit needed: Add 'AI_API_KEY' to your Streamlit Secrets first!")
    st.stop()

# 2. Setup Gallery Folder
if not os.path.exists("gallery"):
    os.makedirs("gallery")

# 3. User Upload Spot
uploaded_file = st.file_uploader("Upload Image to Animate", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Preview input image
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Source", width=300)
    
    # 4. Motion Description
    motion_prompt = st.text_area("Describe the motion physics:", 
                                placeholder="e.g., Kinetic hair movement, slow camera zoom in, cinematic flickers...")

    if st.button("Generate Unrestricted Video"):
        with st.spinner("Bypassing filters... rendering motion..."):
            try:
                # Setup Auth
                api_key = st.secrets["AI_API_KEY"]
                api_url = "https://api.kie.ai/api/v1/runway/generate"
                
                # Convert PIL Image to Base64
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # Payload: enableTranslation allows for multilingual prompts if needed
                payload = {
                    "prompt": motion_prompt,
                    "imageUrl": f"data:image/jpeg;base64,{img_b64}",
                    "model": "runway-gen3-alpha-turbo",
                    "duration": 5,
                    "aspectRatio": "16:9"
                }

                # Submit the Generation Task
                submit_res = requests.post(api_url, json=payload, headers=headers).json()
                
                if submit_res.get("code") == 200:
                    task_id = submit_res["data"]["taskId"]
                    st.info(f"Task Submitted: {task_id}. Animating pixels...")
                    
                    # 5. Polling for Result
                    status_url = f"https://api.kie.ai/api/v1/runway/record-info?taskId={task_id}"
                    
                    for i in range(25): # Loop for ~125 seconds
                        time.sleep(5)
                        res = requests.get(status_url, headers=headers).json()
                        
                        # successFlag: 0=Generating, 1=Success, 2=Failed
                        if res["data"]["successFlag"] == 1:
                            # resultUrls is a JSON string of a list
                            final_urls = eval(res["data"]["resultUrls"])
                            video_url = final_urls[0]
                            
                            st.
