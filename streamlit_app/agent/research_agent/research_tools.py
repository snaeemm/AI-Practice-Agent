"""
Research Agent Tools - Google Search powered
Provides 4 specialized search tools for market intelligence
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .google_search import get_search_client


def tool_search_trending_topics(
    industry: str,
    keywords: List[str] = [],
    platform: str = 'general',
    time_range: str = 'week'
) -> Dict[str, Any]:
    """
    Search for trending topics and recent news in an industry

    Called by: Marketing agent for trend-based content ideas

    Args:
        industry: Industry to research (e.g., "AI", "healthcare", "fintech")
        keywords: Optional specific themes to focus on (e.g., ["innovation", "leadership"])
        platform: 'general', 'linkedin', 'tech_news', 'twitter'
        time_range: 'day', 'week', 'month'

    Returns:
        {
            'success': True,
            'trending_topics': [
                {
                    'title': '...',
                    'snippet': '...',
                    'url': '...',
                    'source': '...',
                    'relevance': 'high/medium/low'
                },
                # ...
            ],
            'summary': '8 trending topics found',
            'searches_used': 2
        }
    """
    try:
        search_client = get_search_client()

        if not search_client.is_configured():
            return {
                'success': False,
                'error': 'Google Search API not configured',
                'trending_topics': [],
                'searches_used': 0
            }

        # Determine date restriction based on time_range
        date_restrict_map = {
            'day': 'd1',
            'week': 'd7',
            'month': 'm1'
        }
        date_restrict = date_restrict_map.get(time_range, 'd7')

        # Determine platform-specific search strategy
        platform_config = {
            'general': {
                'sites': ['techcrunch.com', 'theverge.com', 'wired.com'],
                'query_template': '{industry} trends {date}'
            },
            'linkedin': {
                'sites': ['linkedin.com'],
                'query_template': '{industry} insights {date}'
            },
            'tech_news': {
                'sites': ['techcrunch.com', 'venturebeat.com'],
                'query_template': '{industry} news {date}'
            },
            'twitter': {
                'sites': ['twitter.com'],
                'query_template': '{industry} trending {date}'
            }
        }

        config = platform_config.get(platform, platform_config['general'])

        # Build search queries
        current_date = datetime.now().strftime('%B %Y')
        base_query = config['query_template'].format(industry=industry, date=current_date)

        all_results = []
        searches_used = 0

        # Search 1: General trends
        print(f"\n🔍 Search 1: {base_query}")
        result1 = search_client.search(
            query=base_query,
            num_results=10,
            cache_ttl_hours=6,  # Trends cached for shorter time
            date_restrict=date_restrict
        )

        if result1['success']:
            all_results.extend(result1['results'])
            searches_used += 0 if result1.get('cached') else 1

        # Search 2: Keyword-specific trends (if keywords provided)
        if keywords:
            keyword_query = f"{industry} {' OR '.join(keywords[:3])} latest"
            print(f"\n🔍 Search 2: {keyword_query}")
            result2 = search_client.search(
                query=keyword_query,
                num_results=10,
                cache_ttl_hours=6,
                date_restrict=date_restrict
            )

            if result2['success']:
                all_results.extend(result2['results'])
                searches_used += 0 if result2.get('cached') else 1

        # Deduplicate and score results
        seen_urls = set()
        unique_results = []

        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])

                # Simple relevance scoring
                relevance = 'medium'
                snippet_lower = result['snippet'].lower()
                title_lower = result['title'].lower()

                # High relevance if keywords match
                if any(kw.lower() in title_lower or kw.lower() in snippet_lower for kw in keywords):
                    relevance = 'high'
                # Check for trend indicators
                elif any(word in title_lower for word in ['trending', 'hot', 'latest', 'new', 'emerging']):
                    relevance = 'high'

                unique_results.append({
                    'title': result['title'],
                    'snippet': result['snippet'],
                    'url': result['url'],
                    'source': result['source'],
                    'relevance': relevance
                })

        # Sort by relevance
        unique_results.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['relevance'], 2))

        # Limit to top results
        top_results = unique_results[:10]

        summary = f"Found {len(top_results)} trending topics in {industry}"
        if keywords:
            summary += f" (focused on: {', '.join(keywords[:3])})"

        return {
            'success': True,
            'trending_topics': top_results,
            'summary': summary,
            'industry': industry,
            'keywords': keywords,
            'platform': platform,
            'time_range': time_range,
            'searches_used': searches_used
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to search trending topics: {str(e)}",
            'trending_topics': [],
            'searches_used': 0
        }


def tool_search_company_info(
    company_name: str,
    focus: str = 'overview',
    industry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Research a company - background, news, projects, capabilities

    Called by: Root agent (RFP research), Marketing agent (competitor analysis)

    Args:
        company_name: Company to research
        focus: 'overview', 'recent_news', 'projects', 'capabilities', 'content_strategy', 'all'
        industry: Optional industry context for better search results

    Returns:
        {
            'success': True,
            'company_name': 'Acme Corp',
            'overview': '...',
            'recent_news': [...],
            'recent_projects': [...],
            'capabilities': '...',
            'content_insights': {...},  # if focus='content_strategy'
            'sources': [...],
            'searches_used': 3
        }
    """
    try:
        search_client = get_search_client()

        if not search_client.is_configured():
            return {
                'success': False,
                'error': 'Google Search API not configured',
                'company_name': company_name,
                'searches_used': 0
            }

        result_data = {
            'success': True,
            'company_name': company_name,
            'focus': focus,
            'industry': industry,
            'sources': []
        }

        searches_used = 0

        # Search strategy based on focus
        if focus in ['overview', 'all']:
            # Overview search
            query = f"{company_name} company overview"
            if industry:
                query += f" {industry}"

            print(f"\n🔍 Searching: {query}")
            result = search_client.search(query, num_results=5, cache_ttl_hours=168)  # Cache 7 days

            if result['success'] and result['results']:
                overview_text = "\n".join([
                    f"- {item['snippet']}" for item in result['results'][:3]
                ])
                result_data['overview'] = overview_text
                result_data['sources'].extend([item['url'] for item in result['results'][:3]])
                searches_used += 0 if result.get('cached') else 1

        if focus in ['recent_news', 'all']:
            # Recent news search
            query = f"{company_name} news"
            print(f"\n🔍 Searching: {query} (recent)")
            result = search_client.news_search(query, days_back=30, num_results=5)

            if result['success']:
                result_data['recent_news'] = result['results']
                result_data['sources'].extend([item['url'] for item in result['results']])
                searches_used += 0 if result.get('cached') else 1

        if focus in ['projects', 'all']:
            # Recent projects search
            query = f"{company_name} projects case studies"
            if industry:
                query += f" {industry}"

            print(f"\n🔍 Searching: {query}")
            result = search_client.search(query, num_results=5, cache_ttl_hours=168)

            if result['success'] and result['results']:
                result_data['recent_projects'] = result['results']
                result_data['sources'].extend([item['url'] for item in result['results']])
                searches_used += 0 if result.get('cached') else 1

        if focus in ['capabilities', 'all']:
            # Capabilities search
            query = f"{company_name} services capabilities products"
            print(f"\n🔍 Searching: {query}")
            result = search_client.search(query, num_results=5, cache_ttl_hours=168)

            if result['success'] and result['results']:
                capabilities_text = "\n".join([
                    f"- {item['snippet']}" for item in result['results'][:3]
                ])
                result_data['capabilities'] = capabilities_text
                result_data['sources'].extend([item['url'] for item in result['results'][:3]])
                searches_used += 0 if result.get('cached') else 1

        if focus == 'content_strategy':
            # Content strategy search (for marketing competitor analysis)
            query = f"{company_name} site:linkedin.com"
            print(f"\n🔍 Searching: {query}")
            result = search_client.site_search(query, site='linkedin.com', num_results=10)

            if result['success'] and result['results']:
                # Analyze content patterns
                result_data['content_insights'] = {
                    'linkedin_posts': result['results'],
                    'posting_frequency': 'Unknown (requires deeper analysis)',
                    'top_themes': 'See recent posts for themes',
                    'engagement_approach': 'See content style in posts'
                }
                result_data['sources'].extend([item['url'] for item in result['results'][:5]])
                searches_used += 0 if result.get('cached') else 1

        # Deduplicate sources
        result_data['sources'] = list(set(result_data['sources']))[:10]

        result_data['searches_used'] = searches_used
        result_data['summary'] = f"Researched {company_name} with focus on {focus}. Used {searches_used} searches, found {len(result_data['sources'])} sources."

        return result_data

    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to research company: {str(e)}",
            'company_name': company_name,
            'searches_used': 0
        }


def tool_search_topic_data(
    topic: str,
    search_type: str = 'statistics',
    industry: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find supporting data for a topic - stats, expert quotes, examples

    Called by: Marketing agent (data-driven posts), Root agent (validation)

    Args:
        topic: Topic to research
        search_type: 'statistics', 'expert_opinions', 'case_studies', 'examples'
        industry: Optional industry context

    Returns:
        {
            'success': True,
            'topic': '...',
            'findings': [
                {
                    'type': 'statistic',
                    'text': '73% of...',
                    'source': 'Gartner 2025',
                    'url': '...'
                },
                # ...
            ],
            'summary': 'Found 5 statistics',
            'searches_used': 2
        }
    """
    try:
        search_client = get_search_client()

        if not search_client.is_configured():
            return {
                'success': False,
                'error': 'Google Search API not configured',
                'topic': topic,
                'findings': [],
                'searches_used': 0
            }

        # Build query based on search type
        query_templates = {
            'statistics': f"{topic} statistics data {datetime.now().year}",
            'expert_opinions': f"{topic} expert opinion analysis",
            'case_studies': f"{topic} case study success story",
            'examples': f"{topic} examples real-world implementation"
        }

        if industry:
            query_templates = {k: f"{industry} {v}" for k, v in query_templates.items()}

        query = query_templates.get(search_type, f"{topic} {search_type}")

        print(f"\n🔍 Searching: {query}")
        result = search_client.search(
            query=query,
            num_results=10,
            cache_ttl_hours=48,  # Data cached for 2 days
            date_restrict='m6'  # Past 6 months for fresher data
        )

        findings = []
        if result['success']:
            for item in result['results']:
                finding = {
                    'type': search_type.rstrip('s'),  # 'statistics' -> 'statistic'
                    'text': item['snippet'],
                    'source': item['source'],
                    'title': item['title'],
                    'url': item['url']
                }
                findings.append(finding)

        searches_used = 0 if result.get('cached') else 1

        return {
            'success': True,
            'topic': topic,
            'search_type': search_type,
            'industry': industry,
            'findings': findings,
            'summary': f"Found {len(findings)} {search_type.replace('_', ' ')} for {topic}",
            'searches_used': searches_used
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to search topic data: {str(e)}",
            'topic': topic,
            'findings': [],
            'searches_used': 0
        }


def tool_search_industry_standards(
    topic: str,
    industry: str,
    search_for: str = 'best_practices'
) -> Dict[str, Any]:
    """
    Research industry standards, benchmarks, best practices, pricing

    Called by: Root agent (RFP scoping, bid planning)

    Args:
        topic: What to research (e.g., "cloud migration", "CRM implementation")
        industry: Industry context (e.g., "education", "healthcare")
        search_for: 'best_practices', 'pricing_benchmarks', 'timelines', 'standards'

    Returns:
        {
            'success': True,
            'topic': '...',
            'industry': '...',
            'findings': [
                {
                    'category': 'best_practice',
                    'description': '...',
                    'source': '...',
                    'url': '...'
                },
                # ...
            ],
            'summary': 'Found 6 best practices',
            'searches_used': 3
        }
    """
    try:
        search_client = get_search_client()

        if not search_client.is_configured():
            return {
                'success': False,
                'error': 'Google Search API not configured',
                'topic': topic,
                'industry': industry,
                'findings': [],
                'searches_used': 0
            }

        # Build query based on search_for type
        query_templates = {
            'best_practices': f"{topic} {industry} best practices guide",
            'pricing_benchmarks': f"{topic} {industry} pricing cost benchmark",
            'timelines': f"{topic} {industry} implementation timeline duration",
            'standards': f"{topic} {industry} industry standards requirements"
        }

        query = query_templates.get(search_for, f"{topic} {industry} {search_for}")

        print(f"\n🔍 Searching: {query}")
        result = search_client.search(
            query=query,
            num_results=10,
            cache_ttl_hours=168  # Standards cached for 7 days
        )

        findings = []
        if result['success']:
            for item in result['results']:
                finding = {
                    'category': search_for.replace('_', ' '),
                    'description': item['snippet'],
                    'title': item['title'],
                    'source': item['source'],
                    'url': item['url']
                }
                findings.append(finding)

        searches_used = 0 if result.get('cached') else 1

        return {
            'success': True,
            'topic': topic,
            'industry': industry,
            'search_for': search_for,
            'findings': findings,
            'summary': f"Found {len(findings)} {search_for.replace('_', ' ')} for {topic} in {industry}",
            'searches_used': searches_used
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to search industry standards: {str(e)}",
            'topic': topic,
            'industry': industry,
            'findings': [],
            'searches_used': 0
        }
