# 🚀 Streamlit Cloud Deployment Guide

## Prerequisites

1. **GitHub Account** - Your code should be in a GitHub repository
2. **Streamlit Cloud Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **PostgreSQL Database** - A hosted PostgreSQL database (see options below)
4. **Google AI API Key** - Get one from [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## 📋 Step-by-Step Deployment

### 1. Prepare Your Database

You need a **publicly accessible PostgreSQL database**. Options:

#### Option A: Neon (Recommended - Free Tier Available)
1. Go to [neon.tech](https://neon.tech)
2. Create a free account
3. Create a new project
4. Copy the connection string (looks like: `postgresql://username:password@ep-xxx.region.aws.neon.tech/dbname`)

#### Option B: Supabase (Free Tier Available)
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string (make sure to use "Connection pooling" string)

#### Option C: Railway (Paid but simple)
1. Go to [railway.app](https://railway.app)
2. Create a PostgreSQL database
3. Copy the connection string from the database settings

### 2. Run Database Migrations

**IMPORTANT:** Run migrations on your production database before deploying:

```bash
# Set your production database URL
export DATABASE_URL="postgresql://username:password@host:port/database"

# Run migrations
python run_migration.py
```

### 3. Prepare Your Repository

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Verify files are present:**
   - ✅ `requirements.txt`
   - ✅ `app.py`
   - ✅ `.streamlit/config.toml`
   - ✅ All `agent/` files
   - ✅ `related_files/` directory with:
     - `capabilities.json`
     - `qualification_matrix.json`
     - `Bid Plan - [Client Opp Name]_BB_140125.xlsx` (template)

### 4. Deploy to Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Click "New app"**

3. **Configure your app:**
   - **Repository:** Select your GitHub repo
   - **Branch:** `main` (or your default branch)
   - **Main file path:** `streamlit_app/app.py`

4. **Advanced settings → Secrets:**
   Click "Advanced settings" and add your secrets in TOML format:

   ```toml
   # Required Secrets
   GOOGLE_API_KEY = "your-actual-google-api-key"
   DATABASE_URL = "postgresql://user:pass@host:port/db"

   # Optional Secrets
   GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
   DB_POOL_MIN_CONN = "1"
   DB_POOL_MAX_CONN = "10"
   FILES_DIR = "./related_files"
   OUTPUT_DIR = "./output"
   RESULTS_DIR = "./results"
   ```

5. **Click "Deploy"**

### 5. Verify Deployment

After deployment (takes 2-5 minutes):

1. ✅ App loads without errors
2. ✅ Can upload a document
3. ✅ Agent responds to queries
4. ✅ Can download reports
5. ✅ Database connection works

---

## 🔧 Configuration Files

### `requirements.txt`
Already created with all necessary dependencies.

### `.streamlit/config.toml`
Already configured with:
- Theme colors
- Upload size limit (50MB)

### `.streamlit/secrets.toml` (Local Development Only)
For local testing, create this file (it's gitignored):

```toml
GOOGLE_API_KEY = "your-local-api-key"
DATABASE_URL = "postgresql://localhost/your_local_db"
```

---

## 🌍 Environment Variables Required

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | ✅ Yes | Google AI API key | `AIza...` |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `GEMINI_MODEL` | ❌ Optional | Gemini model to use | `gemini-2.5-flash-preview-09-2025` |
| `DB_POOL_MIN_CONN` | ❌ Optional | Min DB connections | `1` |
| `DB_POOL_MAX_CONN` | ❌ Optional | Max DB connections | `20` |
| `FILES_DIR` | ❌ Optional | Related files directory | `./related_files` |
| `OUTPUT_DIR` | ❌ Optional | Output directory | `./output` |
| `RESULTS_DIR` | ❌ Optional | Results directory | `./results` |

---

## 📁 Required Files in Repository

Make sure these files exist in `related_files/` directory:

```
streamlit_app/
├── app.py
├── requirements.txt
├── run_migration.py
├── .streamlit/
│   └── config.toml
├── agent/
│   ├── agent.py
│   ├── tools.py
│   ├── prompts.py
│   ├── file_processor.py
│   └── ... (all other agent files)
├── components/
│   ├── chat.py
│   └── sidebar.py
└── related_files/
    ├── capabilities.json
    ├── qualification_matrix.json
    └── Bid Plan - [Client Opp Name]_BB_140125.xlsx
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError"
- Check `requirements.txt` has all dependencies
- Redeploy the app after updating requirements

### Error: "Database connection failed"
- Verify `DATABASE_URL` is correct in secrets
- Make sure database is publicly accessible
- Check database allows connections from Streamlit Cloud IPs

### Error: "File not found: capabilities.json"
- Ensure `related_files/` directory is in your repository
- Check `FILES_DIR` path in secrets

### App is slow
- Consider upgrading your Streamlit Cloud plan
- Optimize database queries
- Use Neon with connection pooling

### Downloads not working
- Check database has `generated_files` table (run migrations)
- Verify file data is being saved to database

---

## 📊 Post-Deployment

### Monitor Your App
- **Logs:** Check Streamlit Cloud logs for errors
- **Database:** Monitor database connections and storage
- **Usage:** Track API usage in Google AI Studio

### Update Your App
```bash
git add .
git commit -m "Update app"
git push origin main
```
Streamlit Cloud will automatically redeploy.

---

## 🔒 Security Notes

1. **Never commit secrets** - Use `.gitignore` for:
   - `.env`
   - `.streamlit/secrets.toml`
   - Any files with API keys

2. **Database Security:**
   - Use strong passwords
   - Enable SSL connections
   - Use connection pooling

3. **API Key Security:**
   - Use Streamlit Secrets for production
   - Rotate keys regularly
   - Monitor API usage

---

## 💰 Cost Estimate

- **Streamlit Cloud:** Free tier available, paid plans start at $20/month
- **Neon Database:** Free tier (0.5GB storage), paid plans start at $19/month
- **Google AI API:** Pay-per-use, very affordable for moderate usage

---

## ✅ Deployment Checklist

- [ ] Database created and accessible
- [ ] Migrations run on production database
- [ ] `related_files/` uploaded to repository
- [ ] Code pushed to GitHub
- [ ] Streamlit app created on share.streamlit.io
- [ ] Secrets configured correctly
- [ ] App deployed successfully
- [ ] Test upload and qualification
- [ ] Test downloads working
- [ ] Monitor logs for errors

---

## 🆘 Need Help?

- **Streamlit Docs:** https://docs.streamlit.io/deploy/streamlit-community-cloud
- **Streamlit Forum:** https://discuss.streamlit.io/
- **Google ADK Docs:** https://ai.google.dev/
