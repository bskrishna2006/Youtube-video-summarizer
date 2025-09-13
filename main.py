

import re
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
import yt_dlp
import os
from dotenv import load_dotenv

load_dotenv()

# 🔹 Step 0: Load your API Key from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 🔹 Step 1: Extract video ID from YouTube URL
def extract_video_id(url: str) -> str:
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")

# 🔹 Step 2: Fetch captions using yt-dlp (robust for all cases)
def get_captions(url: str, lang='en'):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'subtitleslangs': [lang],
        'subtitlesformat': 'best',  # auto-select best available (vtt, srt)
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles') or info.get('automatic_captions')
            if not subtitles:
                print("❌ No captions available for this video.")
                return None

            # Choose subtitle
            if lang in subtitles:
                sub_info = subtitles[lang]
            else:
                # fallback to first available language
                first_lang = list(subtitles.keys())[0]
                sub_info = subtitles[first_lang]
                print(f"⚠️ Captions not found in {lang}, using {first_lang}")

            # sub_info can be a list of dicts or a dict itself
            if isinstance(sub_info, list):
                sub_url = sub_info[0]['url']  # take the first available
            else:
                sub_url = sub_info['url']

            # Fetch subtitle file
            r = requests.get(sub_url)
            lines = r.text.splitlines()
            # Keep only the text (skip timestamps and numbering)
            text_lines = [line.strip() for line in lines if line and "-->" not in line and not line.isdigit()]
            return " ".join(text_lines)

    except Exception as e:
        print(f"❌ Error fetching captions with yt-dlp: {e}")
        return None

# 🔹 Step 3: Split text into chunks
def split_text(text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_text(text)
def extract_text_from_captions(captions_json):
    """
    Extracts plain text from yt-dlp JSON captions.
    Returns a single string with line breaks.
    """
    text_lines = []
    for event in captions_json.get("events", []):
        for seg in event.get("segs", []):
            if "utf8" in seg:
                text_lines.append(seg["utf8"].replace("\n", " ").strip())
    return " ".join(text_lines)

# 🔹 Step 4: Summarize using Groq LLaMA
def summarize_text(chunks):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # or "llama3-70b-8192"
        temperature=0,
        groq_api_key=GROQ_API_KEY
    )    
    docs = [Document(page_content=chunk) for chunk in chunks]

    chain = load_summarize_chain(llm, chain_type="map_reduce")
    summary = chain.invoke(docs)  # pass Documents instead of strings
    return summary


# 🔹 Main Flow
# 🔹 Main Flow
if __name__ == "__main__":
    url = input("Paste YouTube video link: ")

    try:
        video_id = extract_video_id(url)
        print(f"🎥 Video ID: {video_id}")

        # Get captions JSON (if available)
        captions_text = get_captions(url, lang='en')

        if captions_text:
            # If the captions were JSON events, extract plain text
            if captions_text.strip().startswith("{") and "events" in captions_text:
                import json
                try:
                    captions_json = json.loads(captions_text)
                    captions_text = extract_text_from_captions(captions_json)
                except Exception:
                    pass  # keep original text if parsing fails

            chunks = split_text(captions_text)

            print("\n⚡ Generating summary... (this may take a few seconds)")
            summary = summarize_text(chunks)

            print("\n===== 📌 VIDEO SUMMARY =====\n")
            print(summary)
        else:
            print("❌ Could not fetch captions for this video.")

    except Exception as e:
        print(f"❌ Error: {e}")
