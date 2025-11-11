"""
Cached wrappers for database tools to reduce PostgreSQL queries.
Only READ tools are cached. WRITE tools remain immediate.
"""

from typing import Dict, Any, Optional, List
from .database_tools import (
    tool_query_database,
    tool_get_bid_plan_data,
    tool_get_qualification_data,
    # WRITE tools - NOT cached, imported directly
    tool_update_qualification,
    tool_update_deliverable,
    tool_update_assignment,
    tool_add_deliverable,
    tool_remove_deliverable,
    tool_save_bid_insight
)
from .session_cache import SessionCache


# Global cache instance (will be set by chat.py)
_global_cache: Optional[SessionCache] = None


def set_global_cache(cache: SessionCache):
    """Set the global cache instance"""
    global _global_cache
    _global_cache = cache


def _get_cache() -> SessionCache:
    """Get the global cache instance"""
    if _global_cache is None:
        raise RuntimeError("Cache not initialized. Call set_global_cache() first.")
    return _global_cache


# ==================== CACHED READ TOOLS ====================

def cached_tool_query_database(
    query_type: str,
    rfp_id: Optional[str] = None,
    client_name: Optional[str] = None,
    industry: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    CACHED version of tool_query_database.

    - Caches RFP data for 5 minutes (query_type="rfp")
    - Does NOT cache list queries (query_type="rfps" or "history")
    """
    cache = _get_cache()

    # Only cache single RFP queries
    if query_type == "rfp" and rfp_id:
        # Check cache first
        cached_data = cache.get_rfp_data(rfp_id, 'complete')
        if cached_data is not None:
            return cached_data

        # Cache miss - query DB
        result = tool_query_database(
            query_type=query_type,
            rfp_id=rfp_id,
            client_name=client_name,
            industry=industry,
            outcome=outcome,
            limit=limit
        )

        # Cache successful result
        if result.get('success'):
            cache.set_rfp_data(rfp_id, 'complete', result, ttl_seconds=300)

        return result

    # For list queries, always hit DB (data changes frequently)
    return tool_query_database(
        query_type=query_type,
        rfp_id=rfp_id,
        client_name=client_name,
        industry=industry,
        outcome=outcome,
        limit=limit
    )


def cached_tool_get_bid_plan_data(rfp_id: str) -> Dict[str, Any]:
    """
    CACHED version of tool_get_bid_plan_data.

    Caches deliverables + assignments for 5 minutes.
    """
    cache = _get_cache()

    # Check cache first
    cached_data = cache.get_rfp_data(rfp_id, 'bid_plan')
    if cached_data is not None:
        return cached_data

    # Cache miss - query DB
    result = tool_get_bid_plan_data(rfp_id)

    # Cache successful result
    if result.get('success'):
        cache.set_rfp_data(rfp_id, 'bid_plan', result, ttl_seconds=300)

    return result


def cached_tool_get_qualification_data(rfp_id: str) -> Dict[str, Any]:
    """
    CACHED version of tool_get_qualification_data.

    Caches qualification data for 5 minutes.
    """
    cache = _get_cache()

    # Check cache first
    cached_data = cache.get_rfp_data(rfp_id, 'qualification')
    if cached_data is not None:
        return cached_data

    # Cache miss - query DB
    result = tool_get_qualification_data(rfp_id)

    # Cache successful result
    if result.get('success'):
        cache.set_rfp_data(rfp_id, 'qualification', result, ttl_seconds=300)

    return result


# ==================== WRITE TOOLS (NOT CACHED - IMMEDIATE) ====================

def cached_tool_update_qualification(
    rfp_id: str,
    field_path: str,
    new_value: Any
) -> Dict[str, Any]:
    """
    Update qualification data (IMMEDIATE PostgreSQL write).

    Also invalidates cache for this RFP.
    """
    cache = _get_cache()

    # Execute immediate write
    result = tool_update_qualification(rfp_id, field_path, new_value)

    # Invalidate cache on successful write
    if result.get('success'):
        cache.invalidate_rfp(rfp_id)

    return result


def cached_tool_update_deliverable(
    rfp_id: str,
    deliverable_type: str,
    deliverable_index: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update deliverable (IMMEDIATE PostgreSQL write).

    Also invalidates cache for this RFP.
    """
    cache = _get_cache()

    # Execute immediate write
    result = tool_update_deliverable(rfp_id, deliverable_type, deliverable_index, updates)

    # Invalidate cache on successful write
    if result.get('success'):
        cache.invalidate_rfp(rfp_id)

    return result


def cached_tool_update_assignment(
    rfp_id: str,
    section_name: str,
    new_owner: Optional[str] = None,
    new_reasoning: Optional[str] = None,
    alternative_partners: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update assignment (IMMEDIATE PostgreSQL write).

    Also invalidates cache for this RFP.
    """
    cache = _get_cache()

    # Execute immediate write
    result = tool_update_assignment(
        rfp_id, section_name, new_owner, new_reasoning, alternative_partners
    )

    # Invalidate cache on successful write
    if result.get('success'):
        cache.invalidate_rfp(rfp_id)

    return result


def cached_tool_add_deliverable(
    rfp_id: str,
    deliverable_type: str,
    deliverable_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add deliverable (IMMEDIATE PostgreSQL write).

    Also invalidates cache for this RFP.
    """
    cache = _get_cache()

    # Execute immediate write
    result = tool_add_deliverable(rfp_id, deliverable_type, deliverable_data)

    # Invalidate cache on successful write
    if result.get('success'):
        cache.invalidate_rfp(rfp_id)

    return result


def cached_tool_remove_deliverable(
    rfp_id: str,
    deliverable_type: str,
    deliverable_index: int
) -> Dict[str, Any]:
    """
    Remove deliverable (IMMEDIATE PostgreSQL write).

    Also invalidates cache for this RFP.
    """
    cache = _get_cache()

    # Execute immediate write
    result = tool_remove_deliverable(rfp_id, deliverable_type, deliverable_index)

    # Invalidate cache on successful write
    if result.get('success'):
        cache.invalidate_rfp(rfp_id)

    return result


def cached_tool_save_bid_insight(
    rfp_id: str,
    outcome: str,
    insight_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save bid insight (IMMEDIATE PostgreSQL write).

    No cache invalidation needed (historical data).
    """
    # Execute immediate write (no caching)
    return tool_save_bid_insight(rfp_id, outcome, insight_data)
