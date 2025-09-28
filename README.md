# 🎬 YouTube Video Summarizer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful **AI-driven web application** built with Streamlit that automatically extracts YouTube video transcripts and generates intelligent summaries using **Groq's LLaMA 3.1** model. Transform long videos into concise, actionable insights in seconds!

## ✨ Key Features

### 🎯 **Smart Video Processing**
- **Automatic transcript extraction** using `yt-dlp` for reliable video processing
- **Multi-language support** for videos with available captions
- **Robust error handling** for private videos and missing transcripts
- **Real-time processing** with live progress indicators

### 🤖 **AI-Powered Summarization**
- **Groq LLaMA 3.1-8B** integration for high-quality summaries
- **4 Summary Styles**:
  - 📝 **General Summary** - Comprehensive overview
  - 🔍 **Detailed Summary** - In-depth analysis with key points
  - 📋 **Bullet Points** - Quick, scannable format
  - 🎯 **Key Takeaways** - Essential insights and action items
- **Smart text chunking** for videos of any length (handles token limits automatically)
- **Customizable parameters** for advanced users

### 🎨 **Modern User Interface**
- **Beautiful gradient design** with dark/light mode support
- **Responsive layout** that works on all devices
- **Interactive analytics** showing word counts, compression ratios, and reading time
- **One-click actions**: Copy summary, download as text, or start over
- **Expandable transcript viewer** with proper formatting

### 📊 **Analytics & Insights**
- **Real-time statistics**: Original vs. summary word count
- **Compression ratio** showing efficiency gains
- **Estimated reading time** for quick planning
- **Session analytics** tracking your usage

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Groq API key (free tier available)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/bskrishna2006/Youtube-video-summarizer.git
cd Youtube-video-summarizer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser** and navigate to `http://localhost:8501`

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Advanced Settings
The app includes customizable parameters for power users:
- **Chunk Size**: Adjust text processing size (default: 2500 chars)
- **Max Summary Tokens**: Control summary length (default: 500 tokens)
- **Summary Style**: Choose from 4 different formats

## 📖 Usage Guide

### Basic Usage
1. **Enter YouTube URL** in the main input field
2. **Select summary style** from the sidebar (optional)
3. **Click "🎯 Summarize Video"** and wait for processing
4. **Review your summary** with statistics and full transcript access

### Advanced Features
- **Custom chunk sizes** for handling very long videos
- **Token limit adjustment** for shorter/longer summaries
- **Multiple summary formats** for different use cases
- **Session analytics** to track your productivity

## 🛠️ Technical Architecture

### Core Components
- **Frontend**: Streamlit with custom CSS for modern UI
- **Video Processing**: `yt-dlp` for reliable transcript extraction
- **AI Engine**: Groq LLaMA 3.1-8B for natural language processing
- **Text Processing**: Smart chunking algorithm for large transcripts

### File Structure
```
youtube-video-summarizer/
├── app.py                 # Main Streamlit application
├── main.py               # Command-line version
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (create this)
├── README.md           # This file
└── assets/            # Screenshots and images
```

## 🎯 Use Cases

### 📚 **Education**
- Summarize lecture videos for quick review
- Extract key concepts from educational content
- Create study notes from video lessons

### 💼 **Business**
- Process webinar recordings efficiently
- Extract action items from meeting recordings  
- Analyze competitor presentations

### 📺 **Content Creation**
- Research topics quickly from multiple videos
- Create content briefs from source material
- Analyze trending video content

### 🔬 **Research**
- Process interview recordings
- Extract insights from conference talks
- Analyze video testimonials

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Youtube-video-summarizer.git

# Install development dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest tests/
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq** for providing excellent AI infrastructure
- **Streamlit** for the amazing web framework
- **yt-dlp** developers for reliable video processing
- **LLaMA** team for the powerful language model

## 📞 Support

- 🐛 **Bug Reports**: [Open an issue](https://github.com/bskrishna2006/Youtube-video-summarizer/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/bskrishna2006/Youtube-video-summarizer/discussions)
- 📧 **Contact**: [Email](mailto:your.email@example.com)

## ⭐ Star History

If you find this project helpful, please consider giving it a star! It helps others discover the project.

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/bskrishna2006">Krishna</a></p>
  <p>Transform any YouTube video into actionable insights!</p>
</div>