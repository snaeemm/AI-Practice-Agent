---
title: Granite RFP Bid Assistant
emoji: ⚙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: apache-2.0
---

# Granite RFP Bid Assistant

An AI-powered assistant for managing RFP (Request for Proposal) bids, powered by Google's Gemini AI.

## Features

- **RFP Document Processing:** Upload and analyze RFP documents automatically
- **AI-Powered Chat:** Interactive chat interface with Google Gemini 2.5
- **Qualification Analysis:** Automatic qualification scoring against your capabilities
- **Bid Planning:** Generate comprehensive bid plans with deliverables
- **Marketing Content:** Create social media posts and marketing materials
- **Multi-User Support:** Secure authentication with user sessions
- **PostgreSQL Database:** Persistent storage for all RFPs, users, and session data

## Technology Stack

- **Frontend:** Streamlit (Python-based UI framework)
- **AI Model:** Google Gemini 2.5 Flash with Google ADK (Agent Development Kit)
- **Database:** PostgreSQL (via Neon/Supabase)
- **Authentication:** bcrypt with session management
- **Deployment:** Docker on Hugging Face Spaces

## Usage

1. **Login:** Use your credentials to access the application
   - Default test user: `sharif` / `Password123`

2. **Upload RFP:** Upload an RFP document (PDF/DOCX) for analysis

3. **Chat Interface:** Ask questions about RFPs, generate reports, create marketing content

4. **Marketing Tools:** Navigate to the Marketing page to create social media content

## Configuration

The app requires the following environment variables (set in Hugging Face Space secrets):

- `GOOGLE_API_KEY`: Your Google AI API key (required)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `GEMINI_MODEL`: Gemini model name (optional, defaults to gemini-2.5-flash-preview-09-2025)
- `DB_POOL_MIN_CONN`: Min database connections (optional, default: 1)
- `DB_POOL_MAX_CONN`: Max database connections (optional, default: 10)

## Architecture

This deployment uses Docker SDK on Hugging Face Spaces:
- Docker container running Python 3.11
- Streamlit server on port 8501
- Connects to external PostgreSQL database
- All code symlinked from main `streamlit_app/` directory

## Development

This app is part of a larger project located in the `streamlit_app/` folder.
The `huggingface_app/` folder contains only deployment-specific files (Dockerfile, README)
and symlinks to the actual application code.

## Future Roadmap

- [ ] Migrate to FastAPI backend for async operations
- [ ] Replace Streamlit frontend with Svelte for better performance
- [ ] Add WebSocket support for real-time chat streaming
- [ ] Implement advanced caching and optimization

## License

Apache 2.0

## Links

- GitHub Repository: [AI-Practice-Agent](https://github.com/snaeemm/AI-Practice-Agent)
- Deployment Folder: `huggingface_app/`
- Source Code: `streamlit_app/`
