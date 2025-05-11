#New chatgpt code 
#Let us see if this works 
#Importing the packages 
import streamlit as st
import os
from time import sleep
import requests
import yt_dlp
from yt_dlp import YoutubeDL
from zipfile import ZipFile
from collections import defaultdict

#Creating the original bar
bar = st.progress(0)

#Getting the api key
try:
    api_key = st.secrets["general"]["api_key"]
except KeyError:
    st.error("API key not found, check your secrets configuration.")
    st.stop()


headers = {
    "authorization": api_key,
    "content_type": "application/json"
}

#Creating the function to get the input URL
def get_yt(URL):
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
    bar.progress(20)
    st.success("1. Audio file of your YouTube video has been successfully downloaded as mp3.")
    return "downloaded_audio.mp3"

#Uploading audio 
def upload_audio(filename):
    with open(filename, 'rb') as f:
        response = requests.post(
            'https://api.assemblyai.com/v2/upload',
            headers = {'authorization': api_key},
            files = {'file': f}
        )
    bar.progress(40)
    st.success("2. Audio file has been uploaded to AssemblyAI API.")
    return response.json()['upload_url']

#Creating the function to transcribe speech to text 
def transcribe_yt(filename):
    upload_url = upload_audio(filename)
    transcript_request = {
        "audio_url": upload_url,
        "iab_categories": True,
        "auto_chapters": True,
        "summarization": True,
        "summary_model": "informative",
        "summary_type": "bullets"
    }

    #Calling the API
    transcribe_endpoint = "https://api.assemblyai.com/v2/transcript"
    response = requests.post(transcribe_endpoint, json=transcript_request, headers=headers)
    transcript_id = response.json()['id']
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    status = 'queued'
    bar.progress(60)
    st.success("3. The audio file speech is being converted to text")
    while status not in ('completed', 'error'):
        polling_response = requests.get(polling_endpoint, headers=headers)
        status = polling_response.json()['status']
        sleep(4) 
    
    if status=='error':
        st.error("Transcription failed.")
        return {}
    
    bar.progress(90)
    st.success("4. Transcription complete")
    st.success("5. Text is being compared to safety labels")

    result = polling_response.json()
    zip_file = "transcription.zip"
    with ZipFile(zip_file, 'w') as zipf:
        zipf.writestr("transcription.txt", result.get('text', ''))

    #Parse and build final stats
    final_stats = {}
    if "iab_categories_result" in result and "results" in result ["iab_categories_result"]:
        label_data = defaultdict(list)
        for item in result["iab_categories_result"]["results"]:
            label_data[item["label"].append(item["relevance"])]

        for label, relevance in label_data.items():
            avg_confidence = round(sum(relevance)/len(relevance)*100, 2)
            count = len(relevance)
            severity = "low"
            if avg_confidence > 70: severity = "high"
            elif avg_confidence > 50: severity = "medium"

            #Setting up the final statistics 
            final_stats[label] = {
                "count": count,
                "avg_confidence": avg_confidence,
                "severity": severity
            }
        
        bar.progress(100)
        st.success("6. Analysis completed")
        return final_stats




