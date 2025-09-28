import streamlit as st
import re
import os
import yt_dlp
from groq import Groq
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

# Get the API key from environment
api_key = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq(api_key=api_key)

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
    """Extract video ID from YouTube URL"""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")

def get_video_transcript(url: str, lang: str = "en"):
    """
    Get transcript using yt-dlp (same approach as test.py)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            "skip_download": True,          # do not download video
            "writesubtitles": True,         # download manual captions if available
            "writeautomaticsub": True,      # download auto-generated captions
            "subtitlesformat": "vtt",       # force VTT output
            "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),  # save in temp dir
            "quiet": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                # Download subtitles to temp directory
                ydl.download([url])
                
                # Find the subtitle file
                sub_file = None
                for file in os.listdir(temp_dir):
                    if file.startswith(info["id"]) and file.endswith(".vtt"):
                        sub_file = os.path.join(temp_dir, file)
                        break
                
                if not sub_file:
                    raise Exception("No subtitle file was downloaded. Video may not have captions.")
                
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
                
                raw_text = " ".join(lines)
                clean_text = clean_autogen_transcript(raw_text)
                
                if not clean_text or len(clean_text.strip()) < 50:
                    raise Exception("Extracted transcript is too short or empty")
                
                return clean_text
                
            except Exception as e:
                raise Exception(f"Could not retrieve transcript: {str(e)}")

def chunk_text(text: str, max_chars: int = 2000):
    """
    Split text into smaller chunks to avoid token limits
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > max_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def summarize_with_groq(text: str, summary_type: str = "general"):
    """Summarize text using Groq's LLaMA model with chunking for large texts"""
    if not api_key:
        raise Exception("Groq API key not found. Please add GROQ_API_KEY to your .env file")
    
    # Check if text is too long and needs chunking
    if len(text) > 3000:  # Conservative limit to avoid token issues
        chunks = chunk_text(text, max_chars=2500)
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            try:
                # Summarize each chunk
                prompt = f"Please provide a concise summary of this part of a video transcript:\n\n{chunk}"
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,  # Reduced tokens per chunk
                    temperature=0.1
                )
                
                chunk_summaries.append(response.choices[0].message.content)
                
            except Exception as e:
                raise Exception(f"Error summarizing chunk {i+1}: {str(e)}")
        
        # Combine all chunk summaries
        combined_summary = "\n\n".join(chunk_summaries)
        
        # Create final summary from combined chunks
        final_prompts = {
            "general": f"Please create a cohesive summary from these section summaries of a video:\n\n{combined_summary}",
            "detailed": f"Please create a detailed, well-structured summary from these section summaries:\n\n{combined_summary}",
            "bullet_points": f"Please organize these section summaries into clear bullet points:\n\n{combined_summary}",
            "key_takeaways": f"Please extract the main insights and key takeaways from these summaries:\n\n{combined_summary}"
        }
        
        try:
            final_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": final_prompts[summary_type]}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            # If final summary fails, return the combined chunk summaries
            return combined_summary
    
    else:
        # Original logic for shorter texts
        prompts = {
            "general": f"Please provide a clear and concise summary of the following video transcript:\n\n{text}",
            "detailed": f"Please provide a detailed summary with key points and main topics from the following video transcript:\n\n{text}",
            "bullet_points": f"Please summarize the following video transcript in bullet points, highlighting the main topics:\n\n{text}",
            "key_takeaways": f"Please extract the key takeaways and main insights from the following video transcript:\n\n{text}"
        }
        
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompts[summary_type]}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

# Streamlit UI
def main():
    st.set_page_config(
        page_title="YouTube Video Summarizer",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 YouTube Video Summarizer")
    st.markdown("Enter a YouTube video link to get an AI-generated summary using Groq's LLaMA model.")
    
    # Sidebar for summary options
    with st.sidebar:
        st.header("Summary Options")
        summary_type = st.selectbox(
            "Choose summary style:",
            ["general", "detailed", "bullet_points", "key_takeaways"],
            format_func=lambda x: {
                "general": "General Summary",
                "detailed": "Detailed Summary", 
                "bullet_points": "Bullet Points",
                "key_takeaways": "Key Takeaways"
            }[x]
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("This app uses:")
        st.markdown("- YouTube Transcript API")
        st.markdown("- Groq's LLaMA 3.1-8B model")
        st.markdown("- Streamlit interface")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input field
        url = st.text_input(
            "Paste YouTube video link:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter a valid YouTube video URL"
        )
        
        # Process button
        if st.button("🚀 Summarize Video", type="primary"):
            if not url:
                st.error("Please enter a YouTube video URL")
                return
                
            with st.spinner("Processing video and generating summary..."):
                try:
                    # Step 1: Extract video ID
                    video_id = extract_video_id(url)
                    st.success(f"✅ Video ID extracted: `{video_id}`")
                    
                    # Step 2: Get transcript
                    with st.status("Fetching video transcript...", expanded=False) as status:
                        transcript_text = get_video_transcript(url)  # Pass URL instead of video_id
                        
                        if not transcript_text or len(transcript_text.strip()) < 50:
                            st.error("❌ Could not extract sufficient text from video transcript.")
                            return
                        
                        word_count = len(transcript_text.split())
                        status.update(
                            label=f"✅ Transcript fetched successfully! ({word_count:,} words)",
                            state="complete"
                        )
                    
                    # Step 3: Generate summary
                    with st.status("Generating AI summary...", expanded=False) as status:
                        # Check if chunking will be needed
                        if len(transcript_text) > 3000:
                            estimated_chunks = len(transcript_text) // 2500 + 1
                            status.update(
                                label=f"Processing large transcript in {estimated_chunks} chunks...",
                                state="running"
                            )
                        
                        summary = summarize_with_groq(transcript_text, summary_type)
                        status.update(
                            label="✅ Summary generated successfully!",
                            state="complete"
                        )
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("📌 Video Summary")
                    st.markdown(summary)
                    
                    # Statistics
                    summary_word_count = len(summary.split())
                    compression_ratio = (summary_word_count / word_count) * 100
                    
                    # Stats in columns
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.metric("Original Words", f"{word_count:,}")
                    with stat_col2:
                        st.metric("Summary Words", f"{summary_word_count:,}")
                    with stat_col3:
                        st.metric("Compression", f"{compression_ratio:.1f}%")
                    
                    # Expandable transcript
                    with st.expander("📄 View Full Transcript"):
                        st.text_area(
                            "Complete video transcript:",
                            transcript_text,
                            height=200,
                            disabled=True
                        )
                        
                except ValueError as e:
                    st.error(f"❌ Invalid URL: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Make sure the video has captions/subtitles available and is not private.")
    
    with col2:
        st.markdown("### 📋 How it works")
        st.markdown("""
        1. **Extract Video ID** from YouTube URL
        2. **Fetch Transcript** using YouTube API
        3. **Generate Summary** with Groq LLaMA
        4. **Display Results** with statistics
        """)
        
        st.markdown("### 🎯 Summary Types")
        st.markdown("""
        - **General**: Balanced overview
        - **Detailed**: Comprehensive summary
        - **Bullet Points**: Key points listed
        - **Key Takeaways**: Main insights
        """)
        
        st.markdown("### 🔧 Requirements")
        st.markdown("""
        - Video must have captions/subtitles
        - Video must be publicly accessible
        - Groq API key required
        """)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">Powered by Groq LLaMA 3.1-8B • YouTube Transcript API • Streamlit</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
