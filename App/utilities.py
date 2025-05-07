#Creating the utilities function
#These contain all the functions requried for the transcription, translation and checking of the words with the database from assemblyAI api 
#Importing the packages and libraries required 
import streamlit as st
import os
from time import sleep
import requests
import yt_dlp
from yt_dlp import YoutubeDL
from zipfile import ZipFile

#You are creating a status bar so that they know what is the progress of your transaction 
#Creating the progress bar 
bar = st.progress(0)

#Taking the API 
#Making a try-catch block by chatgpt
try:
    api_key = st.secrets["general"]["api_key"]
    #chatgpt code
    st.write("Available secrets:", st.secrets)

except KeyError:
    st.error("API key not found, check your secrets configuration.")
    st.stop()

#Retrieving the audio file from YouTube video 
# def get_yt(URL):
#     video = YouTube(URL)
#     yt = video.streams.get_audio_only()
#     yt.download()

#     st.info('2. The audio file has been retrieved from your uploaded YouTube video')
#     bar.progress(10)

#Creating the headers:
headers = {
    "authorization": api_key,
    "content_type": "application/json"
}


#Retrieving the audio file from YouTube by using yt_dlp
def get_yt(URL):
    
    #Showing the bar progress
    bar.progress(10)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloaded_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([URL])
    
    #Updating the bar progress
    bar.progress(20)
    st.success("Audio file has been successfully downloaded as mp3.")
    return "downloaded_audio.mp3"
#Uploading the audio file to assemblyAI
#The automatic speech to text translation will be doen by assemblyAI
# def transcribe_yt():
#     current_dir = os.getcwd()

#     for file in os.listdir(current_dir):
#         if file.endswith(".mp4"):
#             mp4_file = os.path.join(current_dir, file)

#     filename = mp4_file
#     bar.progress(20)


#UPLOADING THE AUDIO TO ASSEMBLY AI 
def upload_audio(filename):
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data
    
    upload_url = 'https://api.assemblyai.com/v2/upload'
    response = requests.post(upload_url, headers={"authorization": api_key}, data = read_file(filename))
    bar.progress(40)
    return response.json()['upload_url']


            
#Chatgpt code 
def transcribe_yt(filename):
    bar.progress(30)
    
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data

    headers = {'authorization': api_key}
    response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=read_file(filename))
    audio_url = response.json()['upload_url']
    st.info("3. Audio uploaded to AssemblyAI")
    bar.progress(50)

    # Transcription request with content safety
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = {
        "audio_url": audio_url,
        "content_safety": True,
    }

    transcript_response = requests.post(endpoint, json=json, headers=headers)
    transcript_id = transcript_response.json()['id']
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    st.info("4. Transcribing...")

    while True:
        polling_response = requests.get(polling_endpoint, headers=headers)
        status = polling_response.json()['status']

        if status == 'completed':
            st.success("Transcription completed")
            bar.progress(100)
            break
        elif status == 'error':
            st.error("Transcription failed.")
            return
        sleep(3)

    # Save transcription text
    transcript_text = polling_response.json()['text']
    with open("transcript.txt", "w") as f:
        f.write(transcript_text)

    # Save content safety results
    # Save content safety results
    safety_labels = polling_response.json().get("content_safety_labels", {})
    #Add the debug line to check what it is returning 
    
     # DEBUG: Display the full content safety labels for inspection
    st.subheader("Content Safety Labels")
    st.json(safety_labels)  # This shows the entire JSON content in a pretty format

    # Optionally, process the labels if they exist
    if safety_labels and "results" in safety_labels:
        st.markdown("### Potentially Harmful Content Detected:")
        for result in safety_labels["results"]:
            label = result.get("label", None)
            confidence = result.get("confidence", None)
            severity = result.get("severity", None)
            
            if label and confidence is not None and severity:
                col1, col2, col3 = st.columns([2,4,2])

                with col1:
                    st.markdown(f"**Label:** {label.capitalize()}")
                
                with col2:
                    st.markdown("**Confidence:**")
                    st.progress(int(confidence*100))
                
                with col3:
                    st.markdown("**Severity:**")
                    severity_color = {
                        "low": "🟢 Low",
                        "medium": "🟡 Medium",
                        "high": "🔴 High"
                    }.get(severity.lower(), "⚪ Unkown")
                    st.markdown(f"<div style='font-size:16px'>{severity_color}</div>", unsafe_allow_html=True)
            
            else:
                st.warning("Some content safety results were incomplete or missing expected fields.")
        else:
            st.success("No harmful content detected.")

    # Zip download (optional)
    with ZipFile("transcription.zip", "w") as zipf:
        zipf.write("transcript.txt")
