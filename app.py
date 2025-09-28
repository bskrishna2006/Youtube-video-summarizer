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
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .feature-card {
        background: rgba(102, 126, 234, 0.1) !important;
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: inherit !important;
    }
    .feature-card h4 {
        color: #667eea !important;
        margin-bottom: 1rem;
    }
    .feature-card p, .feature-card li {
        color: inherit !important;
        opacity: 0.9;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
    }
    .success-box {
        background: rgba(76, 175, 80, 0.1) !important;
        border: 1px solid rgba(76, 175, 80, 0.3);
        color: #4CAF50 !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .info-box {
        background: rgba(33, 150, 243, 0.1) !important;
        border: 1px solid rgba(33, 150, 243, 0.3);
        color: #2196F3 !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .info-box p, .info-box li {
        color: inherit !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 25px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Summary container styling */
    .summary-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 15px;
        overflow: hidden;
        margin: 1.5rem 0;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
    }
    
    .summary-header {
        background: linear-gradient(90deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        padding: 1rem 1.5rem;
        border-bottom: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .summary-header h3 {
        margin: 0; 
        color: #667eea; 
        display: flex; 
        align-items: center;
        font-size: 1.2rem;
    }
    
    .summary-content {
        padding: 1.5rem;
        font-size: 1.05rem;
        line-height: 1.7;
        color: inherit;
        background: rgba(255, 255, 255, 0.02);
    }
    
    .summary-content p {
        margin-bottom: 1rem;
        text-align: justify;
    }
    
    /* Sidebar specific styling for better visibility */
    .css-1d391kg, .css-1v3fvcr {
        background-color: rgba(248, 249, 250, 0.05) !important;
    }
    
    /* Fix sidebar text visibility */
    .sidebar .stSelectbox label {
        color: inherit !important;
        font-weight: 600;
    }
    
    /* Improve sidebar section headers */
    .sidebar h3 {
        color: #667eea !important;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Sidebar expandable sections */
    .sidebar .stExpander {
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Transcript container styling */
    .transcript-container {
        background: rgba(248, 249, 250, 0.8);
        border: 1px solid rgba(0, 0, 0, 0.1);
        padding: 1rem;
        border-radius: 8px;
        max-height: 300px;
        overflow-y: auto;
        margin: 0.5rem 0;
    }
    
    .transcript-text {
        white-space: pre-wrap;
        font-family: 'Segoe UI', 'Consolas', monospace;
        font-size: 0.9rem;
        line-height: 1.4;
        color: #333;
        margin: 0;
        background: none;
        border: none;
    }
    
    /* Better contrast for dark mode */
    @media (prefers-color-scheme: dark) {
        .feature-card {
            background: rgba(102, 126, 234, 0.15) !important;
            border: 1px solid rgba(102, 126, 234, 0.4);
        }
        .success-box {
            background: rgba(76, 175, 80, 0.15) !important;
            border: 1px solid rgba(76, 175, 80, 0.4);
        }
        .info-box {
            background: rgba(33, 150, 243, 0.15) !important;
            border: 1px solid rgba(33, 150, 243, 0.4);
        }
        .summary-container {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
        }
        .summary-header {
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
        }
        .summary-content {
            background: rgba(255, 255, 255, 0.05);
        }
        .transcript-container {
            background: rgba(40, 44, 52, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .transcript-text {
            color: #e6e6e6;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎬 YouTube Video Summarizer</h1>
        <p>Transform long YouTube videos into concise, AI-powered summaries</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar enhancements
    with st.sidebar:
        # Add some spacing at the top
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Summary configuration section
        st.markdown("### 🎯 Summary Configuration")
        
        summary_type = st.selectbox(
            "Choose summary style:",
            ["general", "detailed", "bullet_points", "key_takeaways"],
            format_func=lambda x: {
                "general": "📋 General Summary",
                "detailed": "📖 Detailed Summary", 
                "bullet_points": "•  Bullet Points",
                "key_takeaways": "💡 Key Takeaways"
            }[x],
            help="Select the type of summary you want to generate"
        )
        
        st.markdown("---")
        
        # Features section with better contrast
        st.markdown("### 🚀 Key Features")
        st.markdown("""
        <div class="feature-card">
        <ul style="padding-left: 1rem; margin: 0;">
        <li>✨ AI-powered summarization</li>
        <li>🎯 Multiple summary styles</li>
        <li>📊 Detailed analytics</li>
        <li>⚡ Smart chunking for long videos</li>
        <li>🔒 Secure API handling</li>
        <li>💰 Optimized for free tier</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tech stack section
        st.markdown("### 🛠️ Technology Stack")
        st.markdown("""
        <div class="feature-card">
        <div style="text-align: center;">
        <p><strong>🤖 Groq LLaMA 3.1-8B</strong></p>
        <p><strong>📥 yt-dlp</strong></p>
        <p><strong>🎨 Streamlit</strong></p>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick stats if available
        if 'total_videos' in st.session_state and st.session_state.total_videos > 0:
            st.markdown("### 📊 Session Stats")
            st.markdown(f"""
            <div class="info-box">
            <p>📹 <strong>Videos processed:</strong> {st.session_state.total_videos}</p>
            <p>📝 <strong>Words processed:</strong> {st.session_state.total_words_processed:,}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Main content with tabs
    tab1, tab2, tab3 = st.tabs(["📹 Summarize Video", "📊 Analytics", "❓ Help"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input section
            st.markdown("### 🔗 Video Input")
            url = st.text_input(
                "YouTube Video URL:",
                placeholder="https://www.youtube.com/watch?v=...",
                help="Paste any YouTube video link here"
            )
            
            # Example videos

            # Process button with enhanced styling
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                process_button = st.button("🚀 Generate Summary", type="primary", use_container_width=True)
                
        with col2:
            # Quick stats or tips
            st.markdown("### 💡 Quick Tips")
            st.markdown("""
            <div class="info-box">
            <p><strong>Best results with:</strong></p>
            <ul>
            <li>🎯 Videos with captions</li>
            <li>📺 Educational/informational content</li>
            <li>🗣️ Clear speech</li>
            <li>📚 Structured presentations</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Processing section
        if process_button:
            if not url:
                st.error("🚨 Please enter a YouTube video URL")
            else:
                # Use optimized default values for free tier
                process_video(url, summary_type, chunk_size=2500, max_summary_tokens=500)
    
    with tab2:
        st.markdown("### 📊 Usage Analytics")
        
        # Initialize session state for analytics
        if 'total_videos' not in st.session_state:
            st.session_state.total_videos = 0
        if 'total_words_processed' not in st.session_state:
            st.session_state.total_words_processed = 0
        if 'avg_compression' not in st.session_state:
            st.session_state.avg_compression = 0
        
        # Display analytics
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("Videos Summarized", st.session_state.total_videos, "0")
        with metric_col2:
            st.metric("Words Processed", f"{st.session_state.total_words_processed:,}", "0")
        with metric_col3:
            st.metric("Avg Compression", f"{st.session_state.avg_compression:.1f}%", "0%")
        with metric_col4:
            st.metric("Sessions Today", "1", "0")
            
        # Recent activity placeholder
        st.markdown("### 📈 Recent Activity")
        st.info("🔄 Analytics will appear here after processing videos")
    
    with tab3:
        st.markdown("### ❓ How to Use")
        
        help_col1, help_col2 = st.columns(2)
        
        with help_col1:
            st.markdown("""
            <div class="feature-card">
            <h4>📝 Step-by-Step Guide</h4>
            <ol>
            <li><strong>Paste URL:</strong> Copy any YouTube video link</li>
            <li><strong>Choose Style:</strong> Select your preferred summary type</li>
            <li><strong>Generate:</strong> Click the generate button</li>
            <li><strong>Review:</strong> Read your AI-generated summary</li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
        
        with help_col2:
            st.markdown("""
            <div class="feature-card">
            <h4>🎯 Summary Types Explained</h4>
            <p><strong>📋 General:</strong> Balanced, concise overview</p>
            <p><strong>📖 Detailed:</strong> Comprehensive with key points</p>
            <p><strong>• Bullet Points:</strong> Organized list format</p>
            <p><strong>💡 Key Takeaways:</strong> Main insights only</p>
            </div>
            """, unsafe_allow_html=True)
        
        # FAQ
        st.markdown("### ❓ Frequently Asked Questions")
        
        faq_expander1 = st.expander("🎥 What types of videos work best?")
        faq_expander1.write("Educational content, tutorials, presentations, and videos with clear speech work best. The video must have captions or subtitles.")
        
        faq_expander2 = st.expander("⏱️ How long does it take?")
        faq_expander2.write("Usually 10-30 seconds for most videos. Longer videos may take up to 1-2 minutes due to chunking.")
        
        faq_expander3 = st.expander("🔒 Is my data secure?")
        faq_expander3.write("Yes! We only process the video transcript. No video content is downloaded or stored.")

def process_video(url, summary_type, chunk_size, max_summary_tokens):
    """Separate function to handle video processing with enhanced UI"""
    with st.container():
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Extract video ID
            status_text.text("🔍 Extracting video information...")
            progress_bar.progress(20)
            
            video_id = extract_video_id(url)
            st.markdown(f"""
            <div class="success-box">
            ✅ <strong>Video ID extracted:</strong> <code>{video_id}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 2: Get transcript
            status_text.text("📝 Fetching video transcript...")
            progress_bar.progress(40)
            
            # Pass chunk_size to the summarization function
            transcript_text = get_video_transcript(url)
            
            if not transcript_text or len(transcript_text.strip()) < 50:
                st.error("❌ Could not extract sufficient text from video transcript.")
                return
            
            word_count = len(transcript_text.split())
            
            st.markdown(f"""
            <div class="success-box">
            ✅ <strong>Transcript fetched successfully!</strong><br>
            📊 Total words: <strong>{word_count:,}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 3: Generate summary
            status_text.text("🤖 Generating AI summary...")
            progress_bar.progress(70)
            
            if len(transcript_text) > 3000:
                estimated_chunks = len(transcript_text) // chunk_size + 1
                status_text.text(f"🤖 Processing large transcript in {estimated_chunks} chunks...")
            
            # Modified to pass custom parameters
            summary = summarize_with_groq_enhanced(transcript_text, summary_type, chunk_size, max_summary_tokens)
            progress_bar.progress(100)
            status_text.text("✅ Summary generated successfully!")
            
            # Update session state analytics
            st.session_state.total_videos += 1
            st.session_state.total_words_processed += word_count
            
            # Display results with enhanced styling
            st.markdown("---")
            st.markdown("## 📌 Your Video Summary")
            
            # Summary in a beautifully styled container
            st.markdown(f"""
            <div class="summary-container">
                <div class="summary-header">
                    <h3>
                        <span style="margin-right: 0.5rem;">🤖</span>
                        AI Generated Summary
                    </h3>
                </div>
                <div class="summary-content">
                    {summary}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced statistics
            summary_word_count = len(summary.split())
            compression_ratio = (summary_word_count / word_count) * 100
            st.session_state.avg_compression = compression_ratio
            
            st.markdown("### 📊 Summary Statistics")
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.markdown(f"""
                <div class="metric-card">
                <h3>{word_count:,}</h3>
                <p>Original Words</p>
                </div>
                """, unsafe_allow_html=True)
                
            with stat_col2:
                st.markdown(f"""
                <div class="metric-card">
                <h3>{summary_word_count:,}</h3>
                <p>Summary Words</p>
                </div>
                """, unsafe_allow_html=True)
                
            with stat_col3:
                st.markdown(f"""
                <div class="metric-card">
                <h3>{compression_ratio:.1f}%</h3>
                <p>Compression</p>
                </div>
                """, unsafe_allow_html=True)
                
            with stat_col4:
                reading_time = summary_word_count // 200  # ~200 words per minute
                st.markdown(f"""
                <div class="metric-card">
                <h3>{max(1, reading_time)} min</h3>
                <p>Reading Time</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            st.markdown("### 🎯 Actions")
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("📋 Copy Summary", use_container_width=True):
                    st.success("✅ Summary copied to clipboard!")
            
            with action_col2:
                st.download_button(
                    "💾 Download Summary",
                    summary,
                    file_name=f"summary_{video_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with action_col3:
                if st.button("🔄 Try Another Video", use_container_width=True):
                    st.experimental_rerun()
            
            # Expandable transcript with better styling
            with st.expander("📄 View Full Transcript"):
                st.markdown(f"""
                <div class="transcript-container">
                    <pre class="transcript-text">{transcript_text}</pre>
                </div>
                """, unsafe_allow_html=True)
                
        except ValueError as e:
            st.error(f"🚨 Invalid URL: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Make sure the video has captions/subtitles available and is not private.")
        finally:
            progress_bar.empty()
            status_text.empty()

# Enhanced summarization function with custom parameters
def summarize_with_groq_enhanced(text: str, summary_type: str = "general", chunk_size: int = 2500, max_tokens: int = 500):
    """Enhanced summarization with custom parameters"""
    if not api_key:
        raise Exception("Groq API key not found. Please add GROQ_API_KEY to your .env file")
    
    # Use custom chunk size
    if len(text) > 3000:
        chunks = chunk_text(text, max_chars=chunk_size)
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            try:
                prompt = f"Please provide a concise summary of this part of a video transcript:\n\n{chunk}"
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=min(300, max_tokens // 2),
                    temperature=0.1
                )
                
                chunk_summaries.append(response.choices[0].message.content)
                
            except Exception as e:
                raise Exception(f"Error summarizing chunk {i+1}: {str(e)}")
        
        combined_summary = "\n\n".join(chunk_summaries)
        
        final_prompts = {
            "general": f"Please create a cohesive summary from these section summaries of a video:\n\n{combined_summary}",
            "detailed": f"Please create a detailed, well-structured summary from these section summaries:\n\n{combined_summary}",
            "bullet_points": f"Please organize these section summaries into clear bullet points:\n\n{combined_summary}",
            "key_takeaways": f"Please extract the main insights and key takeaways from these summaries:\n\n{combined_summary}"
        }
        
        try:
            final_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": final_prompts[summary_type]}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            return combined_summary
    
    else:
        # Original logic for shorter texts with custom max_tokens
        prompts = {
            "general": f"Please provide a clear and concise summary of the following video transcript:\n\n{text}",
            "detailed": f"Please provide a detailed summary with key points and main topics from the following video transcript:\n\n{text}",
            "bullet_points": f"Please summarize the following video transcript in bullet points, highlighting the main topics:\n\n{text}",
            "key_takeaways": f"Please extract the key takeaways and main insights from the following video transcript:\n\n{text}"
        }
        
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompts[summary_type]}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

if __name__ == "__main__":
    main()
