import streamlit as st
import requests
import base64
import time
import io
from PIL import Image

st.set_page_config(page_title="Grit Motion Studio", layout="wide")
st.title("🎬 Uncensored Motion Studio")

# Secret key validation
if 'AI_API_KEY' not in st.secrets:
    st.error("Missing API Key! Add 'AI_API_KEY' to your Streamlit Secrets.")
    st.stop()

# Step 1: User Uploads the "Spot" image
uploaded_file = st.file_uploader("Upload Image to Animate", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Reference", width=300)
    
    # Step 2: Prompt for motion
    motion_prompt = st.text_area("Describe the physics of motion:", 
                                placeholder="e.g., Wind swaying the hair cinematically, lightning flickering...")

    if st.button("Generate Unrestricted Video"):
        with st.spinner("Pushing to Kie.ai engine... bypassing filters..."):
            try:
                # Convert Image to Base64 (Kie needs raw data for image-to-video)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()

                # Step 3: Trigger the Task (Runway Gen-3 Alpha model on Kie)
                api_key = st.secrets["AI_API_KEY"]
                api_url = "https://api.kie.ai/api/v1/runway/generate"
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "prompt": motion_prompt,
                    "imageUrl": f"data:image/jpeg;base64,{img_b64}",
                    "model": "runway-gen3-alpha-turbo", # High speed & cinematic
                    "duration": 5, # 5s is best for trial credits
                    "aspectRatio": "16:9"
                }

                # Submit task
                submit_res = requests.post(api_url, json=payload, headers=headers).json()
                
                if submit_res.get("code") == 200:
                    task_id = submit_res["data"]["taskId"]
                    st.info(f"Task Submitted: {task_id}. Polling for results...")
                    
                    # Step 4: Polling for Status
                    status_url = f"https://api.kie.ai/api/v1/runway/record-info?taskId={task_id}"
                    
                    for _ in range(20): # Check for 100 seconds
                        time.sleep(5)
                        status_res = requests.get(status_url, headers=headers).json()
                        
                        if status_res["data"]["successFlag"] == 1: # SUCCESS
                            video_urls = status_res["data"]["resultUrls"] # JSON string from API
                            final_url = eval(video_urls)[0] # Get the first link
                            st.video(final_url)
                            st.success("Generation Complete! Your video is live.")
                            break
                        elif status_res["data"]["successFlag"] >= 2: # FAIL
                            st.error(f"Generation Failed: {status_res['msg']}")
                            break
