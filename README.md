# YouTube Video Summarizer

A web application that extracts transcripts from YouTube videos and generates concise summaries using a large language model. It is designed to help users quickly understand long videos such as lectures, talks, and webinars without watching them in full.

---

## Features

### Video Processing
- Automatically extracts transcripts from YouTube videos using `yt-dlp`
- Supports videos with available captions in different languages
- Handles long videos by splitting transcripts into manageable chunks
- Includes basic error handling for unavailable or private videos

### Summarization
- Uses Groq’s LLaMA 3.1 model for natural language summarization
- Supports multiple summary formats:
  - General summary
  - Detailed summary
  - Bullet point summary
  - Key takeaways
- Allows basic control over chunk size and output length

### User Interface
- Built with Streamlit
- Simple, responsive layout usable on desktop and mobile
- Displays summary statistics such as word count and compression ratio
- Allows copying and downloading generated summaries

---

## Installation

### Requirements
- Python 3.8 or newer
- A Groq API key

### Setup

Clone the repository:

```bash
git clone https://github.com/bskrishna2006/Youtube-video-summarizer.git
cd Youtube-video-summarizer
Install dependencies:

pip install -r requirements.txt


Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here


Run the application:

streamlit run app.py


Open your browser and go to:

http://localhost:8501

Usage

Paste a YouTube video URL into the input field.

Select a summary format if desired.

Click the summarize button and wait for processing.

View, copy, or download the generated summary.

Configuration

The application allows basic customization through the interface:

Chunk size for transcript processing

Maximum length of the generated summary

Choice of summary format

Project Structure
youtube-video-summarizer/
├── app.py
├── main.py
├── requirements.txt
├── .env
└── README.md

Use Cases

Reviewing lecture recordings

Summarizing webinars and talks

Extracting key points from long tutorials

Supporting research and content analysis

Contributing

Contributions are welcome.

Fork the repository

Create a new branch

Make your changes

Submit a pull request

License

This project is licensed under the MIT License.

Acknowledgments

Groq for providing the language model infrastructure

Streamlit for the web application framework

yt-dlp for transcript extraction
