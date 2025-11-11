# Google Search Setup Guide

## Overview

The Google Search functionality has been migrated from `google.adk.tools.google_search` to a custom implementation using the **Google Custom Search JSON API**. This provides:

- ✅ Better compatibility with custom tools
- ✅ Result caching to save API quota
- ✅ Fine-grained control over search parameters
- ✅ Support for site-specific and date-restricted searches

## Files Changed

1. **[streamlit_app/agent/agent.py](streamlit_app/agent/agent.py)**
   - Removed: `from google.adk.tools import google_search`
   - Added: `from agent.search_tool import tool_google_search`
   - Updated: `root_agent` tools list to use `tool_google_search`

2. **[streamlit_app/agent/marketing_agent/marketing_agent.py](streamlit_app/agent/marketing_agent/marketing_agent.py)**
   - Removed: `from google.adk.tools import google_search`
   - Added: `from agent.search_tool import tool_google_search`
   - Updated: `marketing_agent` tools list to use `tool_google_search`

## Google Custom Search API Setup

### Step 1: Enable Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services > Library**
4. Search for "Custom Search API"
5. Click **ENABLE**

### Step 2: Create or Configure API Key

**Option A: Use existing API key**
1. Go to **APIs & Services > Credentials**
2. Find your existing API key (currently in `.env`)
3. Click **Edit API key**
4. Under **API restrictions**, select "Restrict key"
5. Enable these APIs:
   - ✅ Custom Search API
   - ✅ Generative Language API (for Gemini)
6. Save changes

**Option B: Create new API key for Custom Search**
1. Go to **APIs & Services > Credentials**
2. Click **CREATE CREDENTIALS > API key**
3. Copy the API key
4. Click **Edit API key** and restrict it to:
   - Custom Search API only
5. Save and update `GOOGLE_SEARCH_API_KEY` in `.env`

### Step 3: Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **Get started** or **Add** to create a new search engine
3. Configure your search engine:
   - **Search engine name**: "AI Agent Web Search" (or any name)
   - **What to search**: Select "Search the entire web"
   - ✅ Enable "Search the entire web" toggle
   - ✅ Enable "Image search" (optional)
4. Click **Create**
5. On the next page, click **Customize** > **Setup**
6. Copy your **Search engine ID** (looks like: `e2e3947d15f4a4b64`)
7. Update `GOOGLE_CSE_ID` in `.env` with this ID

### Step 4: Update Environment Variables

Edit `streamlit_app/agent/.env`:

```bash
# Google Custom Search API
GOOGLE_SEARCH_API_KEY=<your-api-key>     # From Step 2
GOOGLE_CSE_ID=<your-search-engine-id>    # From Step 3
```

### Step 5: Test the Configuration

Run the test script:

```bash
python test_custom_search.py
```

Expected output:
```
✅ Search successful!
   Found 5 results
   Cached: False
   API searches used: 1
```

## Usage in Agents

The custom Google Search tool is now available to:

1. **Root Agent** ([agent.py:71](streamlit_app/agent/agent.py#L71))
   - Automatically available for RFP qualification, bid planning, and general queries

2. **Marketing Agent** ([marketing_agent.py:46](streamlit_app/agent/marketing_agent/marketing_agent.py#L46))
   - Used for trending topics, competitor analysis, and content research

### Tool Parameters

```python
tool_google_search(
    query: str,                      # Search query (required)
    num_results: int = 10,           # Number of results (1-10)
    site: Optional[str] = None,      # Site restriction (e.g., "linkedin.com")
    date_restrict: Optional[str] = None,  # Date filter (e.g., "d7" = past 7 days)
    cache_ttl_hours: int = 24        # Cache TTL in hours
)
```

### Examples

**Trending topics:**
```python
tool_google_search(
    query="AI innovation trends January 2025",
    date_restrict="d7",  # Past 7 days
    cache_ttl_hours=6    # Short cache for fresh content
)
```

**Competitor research:**
```python
tool_google_search(
    query="Microsoft leadership posts",
    site="linkedin.com",
    num_results=10
)
```

**Industry statistics:**
```python
tool_google_search(
    query="cloud migration cost statistics 2025",
    date_restrict="m6",  # Past 6 months
    num_results=10
)
```

## API Quota Management

- **Free tier**: 100 queries/day
- **Paid tier**: $5 per 1,000 queries (up to 10,000/day)
- **Caching**: Results are cached for 24 hours by default (configurable)
- **Quota tracking**: The tool automatically tracks daily usage

To manage quota:
1. Check usage in [Google Cloud Console](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas)
2. Adjust cache TTL to reduce API calls
3. Upgrade to paid tier if needed

## Troubleshooting

### 403 Forbidden Error

**Cause**: API key doesn't have Custom Search API enabled

**Fix**:
1. Go to [Google Cloud Console > API Library](https://console.cloud.google.com/apis/library)
2. Search for "Custom Search API"
3. Click ENABLE
4. Edit your API key and add "Custom Search API" to allowed APIs

### 400 Bad Request

**Cause**: Invalid CSE ID or query syntax

**Fix**:
1. Verify `GOOGLE_CSE_ID` in `.env` matches your search engine ID
2. Check that your search engine is set to "Search the entire web"

### 429 Quota Exceeded

**Cause**: Daily quota limit reached (100 free queries)

**Fix**:
1. Wait until quota resets (midnight Pacific Time)
2. Use cached results (check `.search_cache/` directory)
3. Upgrade to paid tier in [Google Cloud Console](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas)

### No Results Found

**Cause**: Query too specific or CSE configuration issue

**Fix**:
1. Try a broader query
2. Check CSE settings at [Programmable Search Engine](https://programmablesearchengine.google.com/)
3. Ensure "Search the entire web" is enabled

## Benefits of Custom Implementation

### vs. ADK's google_search grounding:

| Feature | ADK Grounding | Custom Tool |
|---------|--------------|-------------|
| Works with custom tools | ❌ May conflict | ✅ Yes |
| Caching | ❌ No | ✅ Yes (24h default) |
| Quota management | ❌ No | ✅ Yes |
| Site-specific search | ❌ No | ✅ Yes |
| Date restrictions | ❌ No | ✅ Yes |
| Error handling | ⚠️ Basic | ✅ Detailed |
| Free tier quota | Unknown | 100/day tracked |

## Next Steps

1. **Enable Custom Search API** in Google Cloud Console
2. **Verify API key permissions** to include Custom Search API
3. **Confirm CSE ID** is correct and set to "Search the entire web"
4. **Run test script**: `python test_custom_search.py`
5. **Test in Streamlit app** with a query like "What are the latest AI trends?"

## Support

If you encounter issues:
1. Check [test_custom_search.py](test_custom_search.py) output for specific errors
2. Review [google_search.py](streamlit_app/agent/google_search.py) implementation
3. Verify configuration at:
   - [Google Cloud Console](https://console.cloud.google.com/)
   - [Programmable Search Engine](https://programmablesearchengine.google.com/)
