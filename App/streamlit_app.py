#This will be the front-end of the application
#Importing all the necessary libraries and packages 
import streamlit as st
import yt_dlp
from utilities import get_yt, upload_audio, transcribe_yt
from PIL import Image

#Importing the function from utilities for visualization 
from utilities import analyze_label_statistics
from utilities import transcribe_yt
from utilities import safety_labels


#Loading the image 
logo = Image.open("Assets/logo.png")

#Creating a layout for the logo and title to be displayed side by side 
col1, col2 = st.columns([4,6])
with col1:
    st.image(logo, width=70)
with col2:
    st.title("Gaming Videos and Website Moderator")


#Creating the front-end 
# st.markdown("Gaming Video and Website Moderator")
# st.title("Gaming Videos and Website Moderator")
st.markdown("Check gaming video and website suitability for your child")
st.warning("Awaiting URL input in the sidebar")

#Creating the sidebar
st.sidebar.header('Check the suitability: ')

with st.sidebar.form(key='my_form'):
    URL = st.text_input("Enter URL of YouTube vides or shorts ")
    submit_button = st.form_submit_button(label="Go")

#Run custom functions if URL is entered 
if submit_button:
    audio_file = get_yt(URL)
    audio_url = upload_audio(audio_file)
    transcribe_yt(audio_file)

    #Adding a try-catch block to see if the zip file does not occur
    try:
        with open("transcription.zip", "rb") as zip_download:
         st.download_button(
            label = "Download ZIP",
            data = zip_download,
            file_name = "transcription.zip",
            mime = "application/zip"
        )
    except FileNotFoundError:
        st.error("Download failed, ZIP file not found.")

with st.sidebar.expander("Refer to the example URL: "):
    st.code("https://www.youtube.com/watch?v=ARECxDukHvE")


#Assuming 'safety_labels' is the JSON you get from the API 
results = safety_labels.get("results", [])
if results:
    st.markdown("Statistics of the video")
    stats, is_suitable = analyze_label_statistics(results)

    for entry in stats:
        st.markdown(f"Label: **{entry['label'].capitalize()}**")
        st.markdown(f"- **Average confidence: ** `{entry['average_confidence']* 100:.2f}%")
        st.progress(min(int(entry['average_confidence']*100),100))
        st.markdown(f"- **Common Severity:** `{entry['common_severity'].capitalize()}`")
    
    st.markdown("---")
    if is_suitable:
        st.success("✅ This video is suitable for kids.")
    else:
        st.error("❌ This video is **not** suitable for kids.")
else:
    st.info("ℹ️ No content safety data to show statistics.")
