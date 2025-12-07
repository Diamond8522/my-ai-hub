import streamlit as st
import requests
import base64
from PIL import Image
import io

st.title("🎬 Uncensored Motion Studio")
st.write("Upload a photo and describe the physics of the animation.")

# Upload Widget
uploaded_file = st.file_uploader("Drop your image here", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Preview
    img = Image.open(uploaded_file)
    st.image(img, caption="Static Image Ready for Life", use_container_width=True)
    
    # Prompt for motion
    motion_prompt = st.text_input("Motion Description:", placeholder="e.g., Hair flowing in slow motion, background neon lights flickering...")
    
    if st.button("Generate Unrestricted Video"):
        with st.spinner("Bypassing filters... rendering motion..."):
            # Setup the API key you stored in Secrets
            api_key = st.secrets["AI_API_KEY"]
            
            # THE BRIDGE (Example: Novita.ai or Fal.ai hosting Wan 2.1)
            # Both have 'enable_safety_checker' settings you can flip to False
            api_url = "https://api.novita.ai/v3/async/wan-i2v" 
            
            # Encode image to Base64 to send via JSON
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            payload = {
                "prompt": motion_prompt,
                "image_base64": img_b64,
                "enable_safety_checker": False  # This is the "Grit" switch
            }
            
            # Send to API (Simplified for example)
            # headers = {"Authorization": f"Bearer {api_key}"}
            # response = requests.post(api_url, json=payload, headers=headers)
            
            st.info("Status: Request Sent. Unfiltered video incoming.")
