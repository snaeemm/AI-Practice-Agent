# 🤖 AI-Powered RFP Bid Planning Assistant

An intelligent Streamlit application that uses Google's Gemini AI to analyze RFPs, generate qualification reports, and create comprehensive bid plans.

## ✨ Features

- 📄 **Document Upload**: Upload RFPs in PDF, DOCX, XLSX formats
- 🤖 **AI Agent**: Conversational interface for RFP analysis
- ✅ **Qualification Reports**: Automated scoring against qualification matrix
- 📊 **Bid Plans**: Generate structured bid plans with deliverables and assignments
- 📥 **Excel Downloads**: Download qualification and bid planning reports
- 💾 **Database Storage**: All data persisted in PostgreSQL

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd streamlit_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create `.streamlit/secrets.toml`:
   ```toml
   GOOGLE_API_KEY = "your-api-key"
   DATABASE_URL = "postgresql://localhost/your_db"
   ```

4. **Run database migrations**
   ```bash
   python run_migration.py
   ```

5. **Start the app**
   ```bash
   streamlit run app.py
   ```

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Streamlit Cloud deployment instructions.

### Quick Deployment Steps:

1. Create a PostgreSQL database (Neon, Supabase, or Railway)
2. Run migrations on production database
3. Push code to GitHub
4. Deploy on [share.streamlit.io](https://share.streamlit.io)
5. Configure secrets in Streamlit Cloud dashboard

## 📋 Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | Google AI API key |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |

See [DEPLOYMENT.md](DEPLOYMENT.md) for full list of optional variables.

## 📁 Project Structure

```
streamlit_app/
├── app.py                      # Main Streamlit app
├── requirements.txt            # Python dependencies
├── run_migration.py           # Database migration script
├── verify_deployment.py       # Pre-deployment checks
├── DEPLOYMENT.md              # Deployment guide
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml.template  # Secrets template
├── agent/
│   ├── agent.py               # Main agent logic
│   ├── tools.py               # Agent tools
│   ├── prompts.py             # AI prompts
│   ├── file_processor.py      # Document processing
│   ├── database/              # Database layer
│   ├── processors/            # RFP processors
│   └── report_generators/     # Excel report generators
├── components/
│   ├── chat.py               # Chat interface
│   └── sidebar.py            # Sidebar components
└── related_files/            # Configuration files
    ├── capabilities.json
    ├── qualification_matrix.json
    └── Bid Plan Template.xlsx
```

## 🔧 Configuration Files

### `related_files/capabilities.json`
Defines internal capabilities and partner network for bid assignments.

### `related_files/qualification_matrix.json`
Qualification criteria and scoring rules for RFP evaluation.

### `related_files/Bid Plan Template.xlsx`
Excel template for generating bid plans.

## 🧪 Pre-Deployment Verification

Run the verification script before deploying:

```bash
python verify_deployment.py
```

This checks:
- ✅ Environment variables
- ✅ Required files
- ✅ Dependencies
- ✅ Database connection

## 📊 Database Schema

The app uses PostgreSQL with these main tables:

- `rfp_documents` - RFP metadata
- `rfp_deliverables` - Deliverables data (JSONB)
- `rfp_raw_data` - Raw RFP data (JSONB)
- `rfp_assignments` - Assignment analysis (JSONB)
- `qualification_results` - Qualification reports (JSONB)
- `generated_files` - Excel files for download (bytea)

Migrations are in `agent/database/migrations/`.

## 🛠️ Development

### Adding New Features

1. **New Agent Tool**: Add to `agent/tools.py`
2. **New Processor**: Add to `agent/processors/`
3. **New Report Type**: Add to `agent/report_generators/`

### Database Changes

1. Create new migration in `agent/database/migrations/`
2. Run `python run_migration.py`

## 🐛 Troubleshooting

### Common Issues

**Import errors**: Run `pip install -r requirements.txt`

**Database errors**: Check `DATABASE_URL` and run migrations

**File not found**: Verify `related_files/` directory exists

**API errors**: Verify `GOOGLE_API_KEY` is valid

See [DEPLOYMENT.md](DEPLOYMENT.md) for more troubleshooting tips.

## 📝 License

[Your License Here]

## 👥 Contributors

[Your Name/Team]

## 🆘 Support

For issues or questions:
- Check [DEPLOYMENT.md](DEPLOYMENT.md)
- Review Streamlit logs
- Check database connections
