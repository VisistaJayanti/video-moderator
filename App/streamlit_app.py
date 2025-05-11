#This will be the front-end of the application
#Importing all the necessary libraries and packages 
import streamlit as st
import yt_dlp
from yt_dlp import YoutubeDL
from utilities import get_yt, upload_audio, transcribe_yt
from PIL import Image


#Loading the image 
logo = Image.open("Assets/logo.png")

#Creating a layout for the logo and title to be displayed side by side 
col1, col2 = st.columns([4,6])
with col1:
    st.image(logo, width=70)
with col2:
    st.title("Gaming Videos Moderator")


#Creating the front-end 
# st.markdown("Gaming Video and Website Moderator")
# st.title("Gaming Videos and Website Moderator")
st.markdown("Check gaming video suitability for your child")
st.warning("Awaiting URL input in the sidebar")

#Creating the sidebar
st.sidebar.header('Check the suitability: ')

with st.sidebar.form(key='my_form'):
    URL = st.text_input("Enter URL of YouTube vides or shorts ")
    submit_button = st.form_submit_button(label="Go")

#Run custom functions if URL is entered 
final_stats = {}
if submit_button:
    audio_file = get_yt(URL)
    audio_url = upload_audio(audio_file)
    final_stats = transcribe_yt(audio_file)

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


#Displaying the statistics of the video 
st.subheader("Video Statistics")
if not final_stats:
    st.success("✅ No sensitive content is detected, suitable for children")
else:
    for label, stats in final_stats.items():
        st.write(f"### Label: {label.capitalize()}")
        st.progress(min(int(stats["average_confidence"]), 100))
        st.write(f"Count: {stats['count']}")
        st.write(f"Confidence: {stats['average_confidence']}%")

    severe_labels = [l for l, s in final_stats.items() if s["severity"] in ["high", "medium"]]
    if severe_labels:
        st.error("❌ Not suitable for children")
    else:
        st.success("✅ Suitable for children")
