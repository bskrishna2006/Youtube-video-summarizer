import re
import os
import yt_dlp
import re

def clean_autogen_transcript(text: str) -> str:
    """
    Cleans auto-generated YouTube captions:
    1. Removes <c>...</c> tags
    2. Removes <00:00:00.000> timestamps
    3. Collapses multiple spaces
    """
    # Remove <c>...</c> tags
    text = re.sub(r"</?c>", "", text)

    # Remove timestamps like <00:00:06.480>
    text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

def extract_video_id(url: str) -> str:
    """Return the 11-character YouTube video ID."""
    m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
    if not m:
        raise ValueError("Invalid YouTube URL")
    return m.group(1)


def get_transcript_text(url: str, lang: str = "en") -> str:
    """
    Return plain transcript text for a YouTube video.
    1. Uses yt-dlp to download subtitles (auto or manual) as VTT.
    2. Cleans timestamps and cue numbers.
    """
    ydl_opts = {
        "skip_download": True,          # do not download video
        "writesubtitles": True,         # download manual captions if available
        "writeautomaticsub": True,      # download auto-generated captions
        "subtitlesformat": "vtt",       # force VTT output
        "outtmpl": "%(id)s.%(ext)s",    # save locally with video ID
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # Download subtitles to local file
        ydl.download([url])

    # Determine downloaded subtitle file
    # It can be en.vtt, en-US.vtt, etc.
    sub_file = None
    for file in os.listdir("."):
        if file.startswith(info["id"]) and file.endswith(".vtt"):
            sub_file = file
            break

    if not sub_file:
        raise RuntimeError("No subtitle file was downloaded.")

    # Read and clean VTT file
    lines = []
    with open(sub_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("WEBVTT"):
                continue
            if "-->" in line:
                continue
            if re.match(r"^\d+$", line):
                continue
            lines.append(line)

    # Optionally remove the downloaded VTT
    os.remove(sub_file)
    raw_text = " ".join(lines)
    clean_text = clean_autogen_transcript(raw_text)

    return clean_text
if __name__ == "__main__":
    video_url = input("Paste YouTube link: ").strip()
    try:
        vid = extract_video_id(video_url)
        print("Video ID:", vid)
        transcript = get_transcript_text(video_url, lang="en")
        print("\n=== TRANSCRIPT ===\n")
        print(transcript)  # preview first 2k chars
    except Exception as e:
        print("Error:", e)
