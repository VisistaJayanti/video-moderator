#Creating the utilities function
#These contain all the functions requried for the transcription, translation and checking of the words with the database from assemblyAI api 
#Importing the packages and libraries required 
import streamlit as st
import os
from time import sleep
import requests
import yt_dlp
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
        'quiet': True,
        'outtmpl': 'audio.%(ext)s',
    }

    with yt_dlp.YouTubeDL(ydl_opts) as ydl:
        ydl.download([URL])
    
    #Updating the bar progress
    bar.progress(20)
    st.success("Audio downloaded as 'audio.webm")
    return "audio.webm"
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
def transcribe_yt(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_data = {
        "audio_url": audio_url,
        "content_safety": True
    }

    response = requests.post(endpoint, json=json_data, headers=headers)
    transcript_id = response.json()['id']
    bar.progress(60)

    #Poll for completion
    status = "queued"
    while status not in ["completed", "error"]:
        polling_response = requests.get(f"{endpoint}/{transcript_id}", headers=headers)
        status = polling_response.json()['status']
        sleep(3)

    bar.progress(90)

    if status == "completed":
        result = polling_response.json()
        #Save transcript
        with open("transcript.txt", "w") as f:
            f.write(result["text"])

        #Save content safety analysis
        with open("content_safety.json", "w") as f:
            f.write(str(result["content_safety_labels"]))

        #Zip results
        with ZipFile("transcription.zip", "w") as zipf:
            zipf.write("transcription.txt")
            zipf.write("content_safety.json")

        bar.progress(100)
        st.success("Transcription and content safety completed")
    else:
        st.error("Transcription failed.")


    
  