#This will be the front-end of the application
#Importing all the necessary libraries and packages 
import streamlit as st
from pytube import YouTube
from utilities import get_yt, transcribe_yt
from PIL import Image

#Loading the image 
logo = Image.open("Assets/logo.png")

#Creating a layout for the logo and title to be displayed side by side 
col1, col2 = st.columns([1,5])
with col1:
    st.image(logo, width=60)
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