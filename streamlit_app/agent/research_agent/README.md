# Research Intelligence Agent

A specialized subagent for web search and market intelligence using Google Custom Search API.

## Overview

The Research Intelligence Agent provides real-time web intelligence to other agents in the system:
- **Trending Topics**: Current industry trends and hot topics for content creation
- **Company Research**: Background, news, projects, and capabilities of any company
- **Data Validation**: Statistics, expert opinions, and case studies
- **Industry Standards**: Benchmarks, best practices, pricing, and timelines

## Setup

### 1. Get Google Custom Search API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Custom Search API"
4. Create API credentials (API Key)
5. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Create a new search engine
   - What to search: "Search the entire web"
   - Name your search engine
7. Get your Search Engine ID (CSE ID)

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Google Custom Search API
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here

# Optional configuration
SEARCH_CACHE_DIR=.search_cache
SEARCH_DAILY_QUOTA=100
```

### 3. Test the Integration

```bash
# The agent will automatically use cached results when available
# Free tier: 100 searches/day
```

## Architecture

```
research_agent/
├── __init__.py                  # Module exports
├── research_agent.py            # Agent definition
├── research_tools.py            # 4 search tools
├── research_prompts.py          # Agent instructions
├── google_search.py             # API wrapper with caching
└── README.md                    # This file
```

## Tools Available

### 1. `tool_search_trending_topics(industry, keywords, platform, time_range)`
Find current trending topics and news in an industry.

**Example:**
```python
tool_search_trending_topics(
    industry="AI",
    keywords=["innovation", "leadership"],
    platform="linkedin",
    time_range="week"
)
```

### 2. `tool_search_company_info(company_name, focus, industry)`
Research any company: background, news, projects, capabilities.

**Example:**
```python
tool_search_company_info(
    company_name="Microsoft",
    focus="content_strategy",
    industry="technology"
)
```

### 3. `tool_search_topic_data(topic, search_type, industry)`
Find supporting data: statistics, expert opinions, case studies.

**Example:**
```python
tool_search_topic_data(
    topic="AI adoption in healthcare",
    search_type="statistics",
    industry="healthcare"
)
```

### 4. `tool_search_industry_standards(topic, industry, search_for)`
Research industry benchmarks, best practices, pricing, timelines.

**Example:**
```python
tool_search_industry_standards(
    topic="cloud migration",
    industry="education",
    search_for="pricing_benchmarks"
)
```

## How Other Agents Use Research

### Marketing Agent
When user asks "What's trending?", marketing agent requests:
```
"I need to research current trends in AI. Let me request the research agent."
→ Root agent delegates to research_intelligence
→ Results returned to marketing agent
→ Marketing agent creates trend-based content suggestions
```

### Root Agent (RFP Processing)
When qualifying RFP and needs client context:
```
User uploads "KHDA RFP"
→ Root agent delegates to research_intelligence: "Research KHDA - background, projects"
→ Research agent returns client intelligence
→ Root agent uses enhanced context for better GO/NO-GO decision
```

## Caching & Quota Management

- **Automatic caching**: Results cached 24h-7d based on content type
- **Quota tracking**: Tracks daily usage (100 free searches/day)
- **Cache hits don't count**: Cached results don't use API quota
- **Smart caching**: Trends cached 6-24h, company info cached 7 days

**Typical usage:**
- User with 3 posts/week: ~5 searches/month
- Heavy user (5 RFPs + daily posts): ~35 searches/month
- Well within free tier limits

## Error Handling

**API not configured:**
```json
{
  "success": false,
  "error": "Google Search API not configured. Set GOOGLE_SEARCH_API_KEY and GOOGLE_CSE_ID"
}
```

**Quota exceeded:**
```json
{
  "success": false,
  "error": "API quota exceeded (100/day free tier). Using cached results when available."
}
```

## Agent Communication Flow

```
User → Marketing Agent: "What's trending in AI?"
Marketing Agent: "I need research on AI trends"
→ Root Agent intercepts
→ Root Agent → Research Agent: "Find trending AI topics"
→ Research Agent searches Google
→ Research Agent → Root Agent: Returns 8 trending topics
→ Root Agent → Marketing Agent: Forwards results
→ Marketing Agent → User: "Here are 3 timely post ideas..."
```

## Benefits

✅ **Real-time intelligence**: Current trends and news
✅ **Competitive insights**: Analyze any company
✅ **Data-driven content**: Statistics and citations
✅ **Industry benchmarks**: Standards and pricing
✅ **Free tier sufficient**: 100 searches/day covers most use cases
✅ **Smart caching**: Minimizes API usage
✅ **Isolated module**: All search logic in one place

## Troubleshooting

**Issue**: "API not configured" error
**Solution**: Set `GOOGLE_SEARCH_API_KEY` and `GOOGLE_CSE_ID` in `.env`

**Issue**: "Quota exceeded" error
**Solution**: Wait 24h for reset, or upgrade to paid tier ($5/1000 queries)

**Issue**: No results found
**Solution**: Try broader search terms or different time ranges

**Issue**: Cached results outdated
**Solution**: Delete `.search_cache` directory to force refresh

## Future Enhancements

- [ ] Advanced query optimization
- [ ] Multi-language support
- [ ] Image search capabilities
- [ ] News-specific search endpoints
- [ ] Competitor tracking dashboards
- [ ] Trend analysis and predictions
