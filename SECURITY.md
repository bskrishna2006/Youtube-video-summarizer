# Security Guidelines for YouTube Video Summarizer

## API Key Management

This document outlines security best practices for handling API keys and sensitive information in this project.

### ⚠️ NEVER commit API keys or secrets to the repository!

### Recommended Practices

#### 1. Environment Variables
Store API keys in environment variables or `.env` files:

```bash
# Create a .env file (already in .gitignore)
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

#### 2. Configuration Template
Create a `config.template.json` file with placeholder values:

```json
{
  "youtube_api_key": "YOUR_YOUTUBE_API_KEY_HERE",
  "openai_api_key": "YOUR_OPENAI_API_KEY_HERE"
}
```

#### 3. Code Examples

**✅ Good Practice:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
if not YOUTUBE_API_KEY:
    raise ValueError("YouTube API key not found in environment variables")
```

**❌ Bad Practice:**
```python
# NEVER do this!
YOUTUBE_API_KEY = "AIzaSyC4K8J2N3M5P7Q9R1S6T8U0V2W4X6Y0Z"
```

### Security Checklist

- [ ] API keys stored in environment variables or `.env` files
- [ ] `.env` files added to `.gitignore`
- [ ] No hardcoded secrets in source code
- [ ] Configuration templates provided for setup
- [ ] Regular security scans performed

### Detection Commands

Run these commands to check for accidentally committed secrets:

```bash
# Search for potential API keys
grep -r -i -E "(api_key|apikey|secret|token|password)" . --exclude-dir=.git

# Search for specific patterns
grep -r -E "[A-Za-z0-9]{32,}" . --exclude-dir=.git
```

### Git Hooks (Optional)

Consider setting up pre-commit hooks to prevent accidental commits:

```bash
#!/bin/sh
# .git/hooks/pre-commit
if grep -r -E "(api_key|apikey|secret|token|password)" . --exclude-dir=.git; then
    echo "Error: Potential API key found in commit!"
    exit 1
fi
```

### If You Accidentally Commit a Secret

1. **Immediately revoke** the compromised API key
2. Generate a new API key
3. Remove the secret from git history:
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch <file-with-secret>' \
   --prune-empty --tag-name-filter cat -- --all
   ```
4. Force push to all remotes
5. Notify team members to re-clone the repository

### Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Git-secrets tool](https://github.com/awslabs/git-secrets)
- [Trufflesaw for secret detection](https://github.com/trufflesecurity/trufflehog)