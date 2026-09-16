import streamlit as st
import cv2
import os
import asyncio
import edge_tts
from PIL import Image
import google.generativeai as genai
import subprocess
import json
import glob

st.set_page_config(page_title="Auto-Sync Video Studio", page_icon="🎬", layout="centered")

st.title("🎬 Chunk-Based Auto-Sync Video & Myanmar Voiceover Studio")
st.markdown("ဆယ်မိနစ်စာ ဗီဒီယိုများကို **၁ မိနစ်စီ အခန်းခွဲ (Chunks)** လုပ်ဆောင်ပြီး အသံနှင့် စာတန်းထိုးများကို တစ်ပိုင်းချင်း အတိအကျချိန်ကိုက်ကာ နောက်ဆုံးတွင် ဗီဒီယိုတစ်ပုဒ်တည်းအဖြစ် အလိုအလျောက် ပေါင်းစပ်ပေးမည်။")

api_key = st.text_input("🔑 Google Gemini API Key ထည့်ရန်", type="password")

voice_style = st.selectbox(
    "🎙️ မြန်မာအသံပုံစံ ရွေးချယ်ရန်",
    [
        "Female - Nilar (Myanmar Soft & Clear)",
        "Male - Thiha (Myanmar Deep & Professional)"
    ]
)

speed_val = st.slider("⚡ အသံအမြန်နှုန်း (Speed)", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
enable_anticopyright = st.checkbox("🛡️ Anti-Copyright (မူပိုင်ခွင့်မထိအောင် အလိုအလျောက် ပြုပြင်ရန်)", value=True)

video_file = st.file_uploader("🎥 မူရင်း ဗီဒီယိုဖိုင် တင်ရန်", type=["mp4", "mov", "avi", "mkv"])

def get_media_duration(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception:
        return 10.0

def extract_frames(video_path, max_frames=4):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    pil_images = []
    if total_frames <= 0 or fps <= 0:
        success, frame = cap.read()
        count = 0
        while success and count < 20:
            if count % 3 == 0:
                cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_images.append(Image.fromarray(cv2_rgb))
            success, frame = cap.read()
            count += 1
        cap.release()
        return pil_images[:max_frames]

    step = max(total_frames // max_frames, 1)
    current_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if current_frame % step == 0:
            cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_images.append(Image.fromarray(cv2_rgb))
            if len(pil_images) >= max_frames:
                break
        current_frame += 1
    cap.release()
    return pil_images

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

if st.button("🚀 အပိုင်းလိုက်ခွဲ၍ အလိုအလျောက် ချိန်ကိုက်ဖန်တီးမည်", type="primary"):
    if not api_key:
        st.error("ကျေးဇူးပြု၍ Google Gemini API Key ထည့်ပါ။")
    elif video_file is None:
        st.error("ကျေးဇူးပြု၍ ဗီဒီယိုဖိုင် တင်ပါ။")
    else:
        with st.spinner("ဗီဒီယိုကို လုပ်ဆောင်နေပါပြီ။ ခဏစောင့်ပါ..."):
            video_path = "temp_input_video.mp4"
            with open(video_path, "wb") as f:
                f.write(video_file.getbuffer())
                
            voice_map = {
                "Female - Nilar (Myanmar Soft & Clear)": "my-MM-NilarNeural",
                "Male - Thiha (Myanmar Deep & Professional)": "my-MM-ThihaNeural"
            }
            selected_voice = voice_map.get(voice_style, "my-MM-NilarNeural")
            speed_rate = f"{int((speed_val - 1.0) * 100):+d}%"
            
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.6-flash')
                
                chunk_pattern = "chunk_%03d.mp4"
                split_cmd = [
                    "ffmpeg", "-y", "-i", video_path,
                    "-c", "copy", "-map", "0",
                    "-segment_time", "60",
                    "-f", "segment", "-reset_timestamps", "1",
                    chunk_pattern
                ]
                subprocess.run(split_cmd, check=True)
                
                chunk_files = sorted(glob.glob("chunk_*.mp4"))
                processed_chunks = []
                global_subtitle_index = 1
                all_full_responses = []
                total_time_offset = 0.0
                master_srt_content = ""
                
                for idx, chunk_file in enumerate(chunk_files):
                    chunk_duration = get_media_duration(chunk_file)
                    frames = extract_frames(chunk_file)
                    
                    prompt = (
                        f"You are a professional video recap creator. Analyze these video frames for segment {idx+1}. "
                        "Provide your output strictly in two separate sections:\n"
                        "1. [MYANMAR_VOICEOVER]: Write a short, natural, engaging video recap script in pure Myanmar language for this specific 1-minute segment.\n"
                        "2. [ENGLISH_SUBTITLES]: Provide short, neat, movie-style English subtitle lines corresponding to this segment, line by line."
                    )
                    
                    contents = [prompt, *frames]
                    response = model.generate_content(contents)
                    full_resp = response.text
                    all_full_responses.append(f"--- Part {idx+1} ---\n" + full_resp)
                    
                    myanmar_text = ""
                    english_lines = []
                    
                    current_section = None
                    for line in full_resp.split('\n'):
                        line_str = line.strip()
                        if "MYANMAR_VOICEOVER" in line_str:
                            current_section = "myanmar"
                            continue
                        elif "ENGLISH_SUBTITLES" in line_str:
                            current_section = "english"
                            continue
                            
                        if current_section == "myanmar" and line_str:
                            myanmar_text += " " + line_str
                        elif current_section == "english" and line_str and not line_str.startswith('*'):
                            clean_line = line_str.lstrip("0123456789.-* ")
                            if clean_line:
                                english_lines.append(clean_line)
                                
                    if not myanmar_text.strip():
                        myanmar_text = "ဤ အပိုင်းတွင် ဆက်လက်ကြည့်ရှုစရာများ ရှိနေပါသည်။"
                    if not english_lines:
                        english_lines = [f"Part {idx+1} Recap", "Amazing scene"]
                        
                    chunk_audio = f"audio_{idx}.mp3"
                    communicate = edge_tts.Communicate(myanmar_text.strip(), selected_voice, rate=speed_rate)
                    asyncio.run(communicate.save(chunk_audio))
                    
                    audio_duration = get_media_duration(chunk_audio)
                    num_lines = len(english_lines)
                    segment_duration = audio_duration / num_lines if num_lines > 0 else audio_duration
                    
                    for i, line in enumerate(english_lines, 1):
                        start_t = total_time_offset + (i - 1) * segment_duration
                        end_t = total_time_offset + (i * segment_duration)
                        if end_t > total_time_offset + audio_duration:
                            end_t = total_time_offset + audio_duration
                        master_srt_content += f"{global_subtitle_index}\n{format_time(start_t)} --> {format_time(end_t)}\n{line}\n\n"
                        global_subtitle_index += 1
                        
                    chunk_srt_filename = f"chunk_{idx}.srt"
                    with open(chunk_srt_filename, "w", encoding="utf-8") as f:
                        local_srt = ""
                        for i, line in enumerate(english_lines, 1):
                            st = (i - 1) * segment_duration
                            et = i * segment_duration
                            local_srt += f"{i}\n{format_time(st)} --> {format_time(et)}\n{line}\n\n"
                        f.write(local_srt)
                        
                    speed_factor = chunk_duration / audio_duration if audio_duration > 0 else 1.0
                    v_filters = [f"setpts={1.0/speed_factor}*PTS"]
                    if enable_anticopyright:
                        v_filters.append("eq=brightness=0.02:saturation=1.1:contrast=1.05")
                        v_filters.append("noise=alls=3:allf=t+u")
                    v_filters.append(f"subtitles={chunk_srt_filename}:force_style='FontName=Arial,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=1,Outline=1,Shadow=1,Alignment=2'")
                    
                    video_filter_complex = ",".join(v_filters)
                    audio_filter_complex = "[1:a]volume=1.8"
                    if enable_anticopyright:
                        audio_filter_complex += ",treble=g=3"
                    audio_filter_complex += "[aout]"
                    
                    out_chunk_video = f"out_chunk_{idx}.mp4"
                    chunk_ffmpeg_cmd = [
                        "ffmpeg", "-y",
                        "-i", chunk_file,
                        "-i", chunk_audio,
                        "-filter_complex", f"[0:v]{video_filter_complex}[vout];{audio_filter_complex}",
                        "-map", "[vout]",
                        "-map", "[aout]",
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        "-shortest",
                        out_chunk_video
                    ]
                    subprocess.run(chunk_ffmpeg_cmd, check=True)
                    processed_chunks.append(out_chunk_video)
                    total_time_offset += audio_duration
                    
                list_txt = "file_list.txt"
                with open(list_txt, "w", encoding="utf-8") as f:
                    for chk in processed_chunks:
                        f.write(f"file '{chk}'\n")
                        
                final_output = "final_output.mp4"
                concat_cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_txt,
                    "-c", "copy",
                    final_output
                ]
                subprocess.run(concat_cmd, check=True)
                
                st.success("🎉 ဗီဒီယို ဖန်တီးမှု ပြီးစီးပါပြီ!")
                st.video(final_output)
                
                with open(final_output, "rb") as f:
                    st.download_button("📥 ဗီဒီယိုကို Download ရယူရန်", f, file_name="final_output.mp4", mime="video/mp4")
                    
            except Exception as e:
                st.error(f"အမှားအယွင်း ဖြစ်ပေါ်သွားပါသည်: {e}")