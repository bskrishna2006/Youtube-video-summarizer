# YouTube Video Summarizer

A tool for summarizing YouTube videos using AI.

## Security Notice 🔒

This project handles API keys for various services. Please follow security best practices:

- **Never commit API keys** to the repository
- Store sensitive information in environment variables
- Refer to [SECURITY.md](SECURITY.md) for detailed security guidelines

## Setup

1. Clone the repository
2. Copy `config.template.json` to `config.json` and add your API keys
3. Or create a `.env` file with your environment variables:
   ```
   YOUTUBE_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   ```

## Quick Security Check

Run this command to check for accidentally committed secrets:
```bash
grep -r -i -E "(api_key|apikey|secret|token|password)" . --exclude-dir=.git
```

## Documentation

- [Security Guidelines](SECURITY.md) - **Read this first!**
- API key management best practices
- Configuration setup instructions

## Development

More development instructions will be added as the project grows.

---

⚠️ **Remember**: Always keep your API keys secure and never commit them to version control!