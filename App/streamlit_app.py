#This will be the front-end of the application
#Importing all the necessary libraries and packages 
import streamlit as st
from pytube import YouTube
from utilities import get_yt, transcribe_yt

#Creating the front-end 
st.markdown("Gaming Video and Website Moderator")
st.title("Check gaming video and website suitability for your child")
st.warning("Awaiting URL input in the sidebar")

#Creating the sidebar
st.sidebar.header('Input Parameter')

with st.sidebar.form(key='my_form'):
    URL = st.text_input("Enter URL; of YouTube videos or shorts: ")
    submit_button = st.form_submit_button(label="Go")

#Run custom functions if URL is entered 
if submit_button:
    get_yt(URL)
    transcribe_yt()

    with open("transcription.zip", "rb") as zip_download:
        btn = st.download_button(
            label = "Download ZIP",
            data = zip_download,
            file_name = "transcription.zip",
            mime = "application/zip"
        )

with st.sidebar.expander("Refer to the example URL: "):
    st.code("https://www.youtube.com/watch?v=ARECxDukHvE")