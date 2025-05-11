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

#Importing collections for data visualization
from collections import defaultdict

#You are creating a status bar so that they know what is the progress of your transaction 
#Creating the progress bar 
bar = st.progress(0)

#Taking the API 
#Making a try-catch block by chatgpt
try:
    api_key = st.secrets["general"]["api_key"]
    #chatgpt code
    # st.write("Available secrets:", st.secrets)

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
    st.success("1. Audio file has been successfully downloaded as mp3.")
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
    st.info("2. Audio file uploaded to AssemblyAI API")
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

    st.info("3. Transcribing speech to text")
    st.info("4. Comparing text with safety labels")


    while True:
        polling_response = requests.get(polling_endpoint, headers=headers)
        status = polling_response.json()['status']

        if status == 'completed':
            st.success("5. Transcription completed")
            st.success("6. Analysis completed")
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
    st.subheader("Analysis of the video")
    st.json(safety_labels)  # This shows the entire JSON content in a pretty format


    #CREATING THE VISUALIZATIONS
    def analyze_labels_statistics(results):
        label_stats = defaultdict(lambda: {"total_confidence": 0.0, "count": 0, "severities": []})
        suitability_flag = True

        for result in results:
            label = result.get("label", "").lower()
            confidence = result.get("confidence", 0.0)
            severity = result.get("severity", "").lower()

            if label != "unknown" and confidence>0 and severity!= "unknown":
                label_stats[label]["total_confidence"] += confidence
                label_stats[label]["count"] += 1
                label_stats["severities"].append(severity)

        output_stats = []

        for label, data in label_stats.items():
            avg_confidence = data["total_confidence"]/data["count"]
            common_severity = max(set(data["severities"]), key=data["severities"].count)

            if common_severity in ["medium", "high"] or avg_confidence>0.6:
                suitability_flag = False
            
            output_stats.append({
                "label": label,
                "average_confidence": avg_confidence,
                "common_severity": common_severity,
            })

        return output_stats, suitability_flag

    

    #Assuming 'safety_labels' is the JSON you get from the API 
    results = safety_labels.get("results", [])
    if results:
     st.markdown("Statistics of the video")
     stats, is_suitable = analyze_labels_statistics(results)

     for entry in stats:
         st.markdown(f"Label: **{entry['label'].capitalize()}**")
         st.markdown(f"- **Average confidence: ** {entry['average_confidence']* 100:.2f}%")
         st.progress(min(int(entry['average_confidence']*100),100))
         st.markdown(f"- **Common Severity:** {entry['common_severity'].capitalize()}")
    
     st.markdown("---")
     if is_suitable:
         st.success("✅ This video is suitable for kids.")
     else:
         st.error("❌ This video is **not** suitable for kids.")
    else:
     st.info("ℹ️ No content safety data to show statistics.")


    # Zip download (optional)
    with ZipFile("transcription.zip", "w") as zipf:
        zipf.write("transcript.txt")
