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
import assemblyai as aai

#Importing collections and matplotlib for data visualization
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd

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

def transcribe_yt(filename):
    bar.progress(30)
    
    # Set up AssemblyAI SDK
    aai.settings.api_key = api_key
    transcriber = aai.Transcriber()
    
    st.info("2. Uploading audio to AssemblyAI API")
    bar.progress(40)
    
    # Create transcription configuration with content safety enabled
    config = aai.TranscriptionConfig(
        content_safety=True,
        speech_model=aai.SpeechModel.slam_1
    )
    
    st.info("3. Transcribing speech to text")
    st.info("4. Analyzing content safety")
    
    # Start transcription
    transcript = transcriber.transcribe(filename, config)
    
    if transcript.status == aai.TranscriptStatus.error:
        st.error(f"Transcription failed: {transcript.error}")
        return
    
    st.success("5. Transcription completed")
    st.success("6. Analysis completed")
    bar.progress(100)
    
    # Save transcription text
    with open("transcript.txt", "w") as f:
        f.write(transcript.text)
    
    # Display analysis in UI
    display_safety_analysis(transcript)
    
    # Zip download
    with ZipFile("transcription.zip", "w") as zipf:
        zipf.write("transcript.txt")

def display_safety_analysis(transcript):
    st.header("🔍 Content Safety Analysis")
    
    # Display full transcript in expandable section
    with st.expander("📝 Full Transcript"):
        st.write(transcript.text)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["⚠️ Safety Overview", "🔎 Detailed Results", "📊 Statistics"])
    
    # Tab 1: Safety Overview
    with tab1:
        st.subheader("Safety Summary")
        
        # Display overall confidence scores
        st.write("##### Content Categories Detected")
        if not hasattr(transcript, 'content_safety') or not transcript.content_safety:
            st.info("No content safety data available")
        else:
            # Create a dataframe for better display
            summary_data = {
                "Category": [],
                "Confidence": []
            }
            
            for label, confidence in transcript.content_safety.summary.items():
                label_name = label.name.replace("ContentSafetyLabel.", "").capitalize()
                summary_data["Category"].append(label_name)
                summary_data["Confidence"].append(f"{confidence * 100:.2f}%")
            
            if summary_data["Category"]:
                df = pd.DataFrame(summary_data)
                st.dataframe(df, hide_index=True, use_container_width=True)
                
                # Create bar chart for confidence scores
                fig, ax = plt.subplots(figsize=(10, 5))
                confidence_values = [float(val.strip('%')) / 100 for val in summary_data["Confidence"]]
                ax.barh(summary_data["Category"], confidence_values, color='salmon')
                ax.set_xlim(0, 1)
                ax.set_xlabel('Confidence Score')
                ax.set_title('Content Safety Categories')
                
                # Add percentage labels
                for i, v in enumerate(confidence_values):
                    ax.text(v + 0.01, i, f"{v:.2%}", va='center')
                
                st.pyplot(fig)
                
                # Final safety decision
                is_safe = all(float(conf.strip('%')) < 70 for conf in summary_data["Confidence"])
                
                st.markdown("### 🚨 Safety Decision")
                if is_safe:
                    st.success("✅ This video is suitable for children.")
                else:
                    st.error("❌ This video is not suitable for children.")
                    st.warning("Content with high confidence scores (>70%) for unsafe categories was detected.")
            else:
                st.info("No safety concerns detected in the content.")
                st.success("✅ This video is suitable for children.")
    
    # Tab 2: Detailed Results
    with tab2:
        st.subheader("Detailed Content Analysis")
        
        if not hasattr(transcript, 'content_safety') or not transcript.content_safety.results:
            st.info("No detailed content safety data available")
        else:
            for i, result in enumerate(transcript.content_safety.results):
                with st.expander(f"Segment {i+1} ({format_timestamp(result.timestamp.start)} - {format_timestamp(result.timestamp.end)})"):
                    st.write("##### Transcript:")
                    st.write(f"_{result.text}_")
                    
                    st.write("##### Safety Labels:")
                    labels_data = []
                    
                    for label in result.labels:
                        label_name = label.label.name.replace("ContentSafetyLabel.", "").capitalize()
                        severity = f"{label.severity:.4f}" if isinstance(label.severity, float) else "None"
                        confidence = f"{label.confidence * 100:.2f}%"
                        
                        labels_data.append({
                            "Label": label_name,
                            "Confidence": confidence,
                            "Severity": severity
                        })
                    
                    if labels_data:
                        st.dataframe(pd.DataFrame(labels_data), hide_index=True, use_container_width=True)
                    else:
                        st.info("No safety labels for this segment")
    
    # Tab 3: Statistics
    with tab3:
        st.subheader("Severity Statistics")
        
        if not hasattr(transcript, 'content_safety') or not transcript.content_safety.severity_score_summary:
            st.info("No severity statistics available")
        else:
            severity_data = []
            
            for label, severity_conf in transcript.content_safety.severity_score_summary.items():
                label_name = label.name.replace("ContentSafetyLabel.", "").capitalize()
                
                low_conf = f"{severity_conf.low * 100:.2f}%"
                med_conf = f"{severity_conf.medium * 100:.2f}%"
                high_conf = f"{severity_conf.high * 100:.2f}%"
                
                severity_data.append({
                    "Category": label_name,
                    "Low Severity": low_conf,
                    "Medium Severity": med_conf,
                    "High Severity": high_conf
                })
            
            if severity_data:
                st.dataframe(pd.DataFrame(severity_data), hide_index=True, use_container_width=True)
                
                # Create stacked bar chart for severity distribution
                fig, ax = plt.subplots(figsize=(10, 5))
                categories = [d["Category"] for d in severity_data]
                low_values = [float(d["Low Severity"].strip('%')) / 100 for d in severity_data]
                med_values = [float(d["Medium Severity"].strip('%')) / 100 for d in severity_data]
                high_values = [float(d["High Severity"].strip('%')) / 100 for d in severity_data]
                
                ax.barh(categories, low_values, color='green', label='Low')
                ax.barh(categories, med_values, left=low_values, color='orange', label='Medium')
                ax.barh(categories, high_values, left=[l+m for l,m in zip(low_values, med_values)], color='red', label='High')
                
                ax.set_xlim(0, 1)
                ax.set_xlabel('Confidence Score')
                ax.set_title('Severity Distribution by Category')
                ax.legend(loc='upper right')
                
                st.pyplot(fig)
            else:
                st.info("No severity data available")

def format_timestamp(ms):
    """Convert milliseconds to mm:ss format"""
    seconds = ms // 1000
    minutes = seconds // 60
    seconds %= 60
    return f"{minutes:02d}:{seconds:02d}"
    