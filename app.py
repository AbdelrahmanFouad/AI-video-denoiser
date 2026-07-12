import streamlit as st
import os
import denoise

st.set_page_config(page_title="AI Video Denoiser", page_icon="✨", layout="wide")

st.title("✨ AI Video Denoiser")
st.markdown("Upload up to 5 videos to remove AI-generated noise and artifacts.")

uploaded_files = st.file_uploader("Upload videos", type=['mp4', 'mov', 'mkv', 'avi', 'webm'], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > 5:
        st.error("Please upload a maximum of 5 videos.")
        uploaded_files = uploaded_files[:5]
        
    preset = st.selectbox("Select Denoising Preset", ['balanced', 'fast', 'hq'], index=0)
    
    if st.button("Start Denoising"):
        for uploaded_file in uploaded_files:
            st.subheader(f"Processing: {uploaded_file.name}")
            
            # Save uploaded file temporarily
            temp_input = f"temp_{uploaded_file.name}"
            with open(temp_input, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            progress_bar = st.progress(0)
            
            def update_progress(p):
                progress_bar.progress(p)
                
            success, result = denoise.denoise_video(temp_input, preset, progress_callback=update_progress)
            
            if success:
                output_file = result
                st.success(f"Denoised: {uploaded_file.name}")
                with open(output_file, "rb") as f:
                    st.download_button(f"Download {uploaded_file.name}", f, file_name=f"denoised_{uploaded_file.name}")
            else:
                error_log = result
                st.error(f"Failed to process {uploaded_file.name}")
                st.text_area("FFmpeg Error Log", error_log, height=300)
                
            # Cleanup
            if os.path.exists(temp_input): os.remove(temp_input)
            if os.path.exists(output_file): os.remove(output_file)

st.markdown("---")
st.caption("Powered by FFmpeg & Python")
