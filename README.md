# 🎬 YouTube Video Summarizer

A Streamlit web app that extracts YouTube video transcripts and generates AI-powered summaries using either **Groq LLaMA**. Summaries can be generated in multiple formats such as **general overview, detailed summary, bullet points, or key takeaways**.  

---

## Features

- Extracts **auto-generated or manual YouTube transcripts** using `yt-dlp`.
- Cleans and formats transcripts for better readability.
- Supports **different summary styles**:
  - General
  - Detailed
  - Bullet Points
  - Key Takeaways
- **Chunking for long transcripts** to avoid token or memory limits.
- Can use **Groq LLaMA API** or **Hugging Face Transformer models**.
- **Streamlit interface** for easy input/output.
- Displays statistics: original word count, summary word count, compression ratio.
- Expandable transcript view for reference.

---

## Demo Screenshot

*(Add a screenshot of your Streamlit app here)*

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/youtube-video-summarizer.git
cd youtube-video-summarizer
Steps:

Open the Streamlit app in your browser.

Paste the YouTube video URL.

Select the summary style from the sidebar.

Click "Summarize Video".

View the generated summary, transcript, and statistics.