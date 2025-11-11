"""
Google Custom Search API Wrapper
Handles API calls, caching, rate limiting, and error handling
"""

import requests
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional


class SearchCache:
    """File-based cache for search results"""

    def __init__(self, cache_dir: str = ".search_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str, ttl_hours: int = 24) -> Optional[Dict]:
        """Get cached result if exists and not expired"""
        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    cached_time = datetime.fromisoformat(cached['timestamp'])
                    age_hours = (datetime.now() - cached_time).total_seconds() / 3600

                    if age_hours < ttl_hours:
                        print(f"✅ Using cached result for: {query[:60]}... (age: {age_hours:.1f}h)")
                        return cached['data']
                    else:
                        print(f"⏰ Cache expired for: {query[:60]}... (age: {age_hours:.1f}h > {ttl_hours}h)")
            except Exception as e:
                print(f"⚠️ Cache read error: {e}")

        return None

    def set(self, query: str, data: Dict):
        """Cache search result"""
        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2)
            print(f"💾 Cached result for: {query[:60]}...")
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")

    def clear_old(self, days: int = 30):
        """Clear cache entries older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        cleared = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    cached_time = datetime.fromisoformat(cached['timestamp'])

                    if cached_time < cutoff:
                        cache_file.unlink()
                        cleared += 1
            except Exception:
                pass

        if cleared > 0:
            print(f"🧹 Cleared {cleared} old cache entries")


class GoogleSearch:
    """Google Custom Search API client with caching and rate limiting"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        self.cache_dir = os.getenv("SEARCH_CACHE_DIR", ".search_cache")
        self.cache = SearchCache(self.cache_dir)
        self.daily_quota = int(os.getenv("SEARCH_DAILY_QUOTA", "100"))
        self.usage_count = 0  # Track in-session usage

        if not self.api_key or not self.cse_id:
            print("⚠️ Google Search API not configured")
            print("   Set GOOGLE_SEARCH_API_KEY and GOOGLE_CSE_ID in .env file")

    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return bool(self.api_key and self.cse_id)

    def search(
        self,
        query: str,
        num_results: int = 10,
        cache_ttl_hours: int = 24,
        site: Optional[str] = None,
        date_restrict: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Execute Google search with caching

        Args:
            query: Search query
            num_results: Number of results (max 10 per API call)
            cache_ttl_hours: Cache TTL in hours
            site: Optional site restriction (e.g., "linkedin.com")
            date_restrict: Optional date restriction (e.g., "d7" for past week, "m1" for past month)
            force_refresh: Bypass cache and force new search

        Returns:
            {
                'success': True/False,
                'results': [...],
                'total_results': int,
                'query': str,
                'cached': True/False,
                'error': str (if failed)
            }
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Google Search API not configured. Set GOOGLE_SEARCH_API_KEY and GOOGLE_CSE_ID in .env',
                'results': [],
                'total_results': 0
            }

        # Build cache key with all parameters
        cache_key_parts = [query, str(num_results), site or "", date_restrict or ""]
        cache_key = "|".join(cache_key_parts)

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_result = self.cache.get(cache_key, ttl_hours=cache_ttl_hours)
            if cached_result:
                cached_result['cached'] = True
                return cached_result

        # Build query with site restriction if provided
        full_query = query
        if site:
            full_query = f"site:{site} {query}"

        # Execute API call
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": full_query,
                "num": min(num_results, 10)  # API max is 10 per request
            }

            if date_restrict:
                params["dateRestrict"] = date_restrict

            print(f"🔍 Searching Google: {full_query[:80]}...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse results
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": item.get("displayLink", ""),
                    "date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")
                })

            result = {
                'success': True,
                'results': results,
                'total_results': len(results),
                'query': query,
                'cached': False
            }

            # Cache result
            self.cache.set(cache_key, result)

            # Track usage
            self.usage_count += 1
            remaining = self.daily_quota - self.usage_count

            print(f"✅ Found {len(results)} results")
            print(f"📊 API usage: {self.usage_count} searches used, {remaining} remaining (daily quota: {self.daily_quota})")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            status_code = e.response.status_code if e.response else None

            if status_code == 429 or "quota" in error_msg.lower():
                error_msg = f"API quota exceeded (free tier: {self.daily_quota}/day). Results will be cached and reused."
            elif status_code == 403:
                error_msg = "Invalid API key or insufficient permissions. Check GOOGLE_SEARCH_API_KEY."
            elif status_code == 400:
                error_msg = f"Bad request. Check query syntax: {query[:50]}"

            print(f"❌ Search error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'results': [],
                'total_results': 0,
                'query': query
            }

        except requests.exceptions.Timeout:
            print(f"❌ Search timeout after 10 seconds")
            return {
                'success': False,
                'error': 'Search request timed out. Try again.',
                'results': [],
                'total_results': 0,
                'query': query
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'results': [],
                'total_results': 0,
                'query': query
            }

    def news_search(
        self,
        query: str,
        days_back: int = 7,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """Search recent news (convenience method)"""
        date_restrict = f"d{days_back}"  # d7 = past 7 days, d30 = past 30 days
        return self.search(
            query=query,
            num_results=num_results,
            cache_ttl_hours=6,  # News cached for shorter time
            date_restrict=date_restrict
        )

    def site_search(
        self,
        query: str,
        site: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """Site-specific search (convenience method)"""
        return self.search(
            query=query,
            site=site,
            num_results=num_results,
            cache_ttl_hours=48  # Site-specific searches cached longer
        )

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            'searches_used': self.usage_count,
            'daily_quota': self.daily_quota,
            'remaining': self.daily_quota - self.usage_count,
            'percentage_used': (self.usage_count / self.daily_quota * 100) if self.daily_quota > 0 else 0
        }


# Singleton instance
_search_client: Optional[GoogleSearch] = None


def get_search_client() -> GoogleSearch:
    """Get or create Google Search client singleton"""
    global _search_client
    if _search_client is None:
        _search_client = GoogleSearch()
    return _search_client
