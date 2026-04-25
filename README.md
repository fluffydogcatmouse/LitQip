# LitQip

A simple & elegent agent harness inspired by Claude Code, built with Python.

## Getting Started

```bash
# Install dependencies
uv sync

# Configure environment
mkdir -p ~/.litqip
cp .env.example ~/.litqip/.env
# Edit ~/.litqip/.env with your API keys

# Run
uv run litqip
```

## Project Structure

```
litqip/
├── src/litqip/       # Source code
├── skills/           # User-defined skills
├── .transcripts/     # Compressed conversation storage
└── .docs/            # Project documentation
```
