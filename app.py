import streamlit as st
import requests
from dotenv import load_dotenv
import os
import time
import uuid
import boto3
load_dotenv()

s3 = boto3.client('s3',
                  region_name=os.getenv("S3_REGION"),
                  endpoint_url=os.getenv("S3_ENDPOINT"),
                  aws_access_key_id=os.getenv("S3_KEY"),
                  aws_secret_access_key=os.getenv("S3_SECRET"))

voicelist = {
    "Zee JKT48": "3lqNUSxkrjubOMEOhxuw",
    "Deddy Corbuzier v1": "MEftyihGXS58i6IZ8eIb"
}

avatarlist = {
    "Male": "https://img.okezone.com/okz/500/library/images/2022/12/21/1mo2vtplcl96obrc2v6q_19511.jpg",
    "Female": "https://image.popmama.com/content-images/post/20220927/fakta-keluarga-zee-jkt48-punya-kembaran-laki-laki-dan-ayah-zee-jkt-48-artis-presenter-aktor-fadli-akhmad-0b166b4faa8fa475cf88a8e3142edecd.jpg"
}

def generate_audio(prompt, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY"),
        "Content-Type": "application/json"
    }
    payload = {
        "text": prompt,
        "voice_settings": {
            "similarity_boost": 0.8,
            "stability": 0.3,
            "style": 1,
            "use_speaker_boost": True
        }
    }
    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        if not os.path.exists('results/audio'):
            os.makedirs('results/audio')

        audio_id = str(uuid.uuid4())
        audio_path = f'results/audio/{audio_id}.mp3'
        print(audio_path)
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(response.content)

        with open(audio_path, 'rb') as data:
            s3.upload_fileobj(data, "tts-avatar-mbh", "elevenlabs/" + audio_path, ExtraArgs={'ACL':'public-read'})

        audio_url = f"{os.getenv('S3_ENDPOINT')}/tts-avatar-mbh/elevenlabs/{audio_path}"

        print(f'Audio saved in {audio_url}')
        return audio_url

    else:
        print(f'Failed: {response.text}')
        return None

def generate_video(audio_path, avatar_url, gender):
    print(audio_path)
    url = "https://api.d-id.com/talks"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization" : "Basic " + os.getenv("API_KEY_DID")
    }
    payload = {
        "script": {
            "type": "audio",
            "audio_url": audio_path
        },
        "source_url": avatar_url
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(response)
        if response.status_code == 201:
            print(response.text)
            res = response.json()
            id = res["id"]
            status = "created"
            while status == "created":
                getresponse =  requests.get(f"{url}/{id}", headers=headers)
                print(getresponse)
                if getresponse.status_code == 200:
                    status = res["status"]
                    res = getresponse.json()
                    print(res)
                    if res["status"] == "done":
                        video_url =  res["result_url"]
                    else:
                        time.sleep(10)
                else:
                    status = "error"
                    video_url = "error"
        else:
            video_url = "error"   
    except Exception as e:
        print(e)      
        video_url = "error"      
        
    return video_url

def main():
    st.set_page_config(page_title="Avatar Video Generator", page_icon=":movie_camera:")

    st.title("Generate Avatar Video")

    prompt = st.text_area("Enter Text Prompt", "This is where you type your prompt...")

    voice_options = ["Deddy Corbuzier v1", "Zee JKT48"]
    voice_selection = st.selectbox("Choose Voice", voice_options)
    voice_id = voicelist[voice_selection]

    avatar_options = ["Male", "Female"]
    avatar_selection = st.selectbox("Choose Avatar", avatar_options)
    avatar_url = avatarlist[avatar_selection]

    if st.button("Generate Video"):
        st.text("Generating video...")
        try:
            audio_path = generate_audio(prompt, voice_id)
            print(audio_path)
            print(avatar_url)
            if audio_path:
                video_url = generate_video(audio_path, avatar_url, avatar_selection)
                if video_url != "error":
                    st.text("Video generated!")
                    st.subheader("Generated Video")
                    st.video(video_url)
                else:
                    st.text("Sorry... Try again1")
            else:
                st.text("Sorry... Try again2")
        except Exception as e:
            print(e)
            st.text("Sorry... Try again3")


if __name__ == "__main__":
    main()