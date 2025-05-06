#Creating the utilities function
#These contain all the functions requried for the transcription, translation and checking of the words with the database from assemblyAI api 
#Importing the packages and libraries required 
import streamlit as st
import os
from time import sleep
import requests
from pytube import YouTube
from zipfile import ZipFile

#You are creating a status bar so that they know what is the progress of your transaction 
#Creating the progress bar 
bar = st.progress(0)

#Taking the API 
#Making a try-catch block by chatgpt
try:
    api_key = st.secrets['general']['api_key']
except KeyError:
    st.error("API key not found, check your secrets configuration.")
    st.stop()

#Retrieving the audio file from YouTube video 
def get_yt(inputURL):
    video = YouTube(inputURL)
    yt = video.streams.get_audio_only()
    yt.download()

    st.info('2. The audio file has been retrieved from your uploaded YouTube video')
    bar.progress(10)

#Uploading the audio file to assemblyAI
#The automatic speech to text translation will be doen by assemblyAI
# def transcribe_yt():
#     current_dir = os.getcwd()

#     for file in os.listdir(current_dir):
#         if file.endswith(".mp4"):
#             mp4_file = os.path.join(current_dir, file)

#     filename = mp4_file
#     bar.progress(20)

#Chatgpt code 
def transcribe_yt():
    current_dir = os.getcwd()

    for file in os.listdir(current_dir):
        if file.endswith(".mp4"):
            mp4_file = os.path.join(current_dir, file)
    
    filename = mp4_file
    bar.progress(20)
    
    if not mp4_file:
        st.error("No mp4 file found in the curent directory")
        return
    
    #Reading the file 
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data
    
    #Details for the API key 
    headers = {'authorization': api_key}
    response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=read_file(filename))
    audio_url = response.json()['upload_url']
    st.info('3. Your YouTube audio file has been uploaded to the AssemblyAI API')
    bar.progress(30)

    #Transcribe the uploaded audio file 
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = {
        "audio_url": audio_url,
        "content_safety": True
    }

    headers = {
        "authorization": api_key,
        "content_type": "application/json"
    }

    transcript_input_response = requests.post(endpoint, json=json, headers=headers)
    st.info('4. Transcribing your uploaded file')
    bar.progress(40)

    #Extracting the transcript ID
    transcript_id = transcript_input_response.json()["id"]
    st.info('5. Extract transcript ID')
    bar.progress(50)

    #Retrieve transcription results
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {
        "authorization": api_key,
    }
    transcript_output_response = requests.get(endpoint, headers=headers)
    st.info('6. Retrieving the transcription results')
    bar.progress(60)

    #Checking if the transcription is completed or not 
    st.warning('Transcription is processing...')
    while transcript_output_response.json()['status'] != 'completed':
        sleep(1)
        transcript_output_response = requests.get(endpoint, headers=headers)

    bar.progress(100)


    #You have to print the transcribed test as output 
    st.header('Output')

    with st.expander('Show transcribed text: '):
        st.success(transcript_output_response.json()["text"])
    
    #Saving the transcribed text to a file 
    #Saving as a TXT file 
    yt_txt = open('yt.txt', 'w')
    yt_txt.write(transcript_output_response.json()["text"])
    yt_txt.close()

    #Writing the JSON to the app 
    with st.expander('Show Full Results: '):
        st.write(transcript_output_response.json())

    #Write the content-safety-labels
    with st.expander('Show content safety labels: '):
        st.write(transcript_output_response.json()["content_safety_labels"])

    with st.expander('Summary of content safety labels: '):
        st.write(transcript_output_response.json()["content_safety_labels"]["summary"])

    #Saving as sub rip text (SRT) file 
    srt_endpoint = endpoint + "/srt"
    srt_response = requests.get(srt_endpoint, headers=headers)
    with open("yt.srt", "w") as _file:
        _file.write(srt_response.text)
    

    zip_file = ZipFile('transcription.zip', 'w')
    zip_file.write('yt.txt')
    zip_file.write('yt.srt')
    zip_file.close()

    #Deleting the processed files 
    for file in os.listdir(current_dir):
        if file.endswith(".mp4"):
            os.remove(file)
        if file.endswith(".txt"):
            os.remove(file)
        if file.endswith(".srt"):
            os.remove(file)






