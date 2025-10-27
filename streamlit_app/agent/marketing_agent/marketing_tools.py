"""
Marketing Agent Tools
Provides tools for creating strategies, planning content, and coordinating multi-profile campaigns
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json

from agent.database.db_singleton import get_db
from agent.database.marketing_db_tools import MarketingDatabaseTools
from agent.database.marketing_profile_manager import MarketingProfileManager
from agent.session_context import get_current_user_id


# Initialize database connections
db = get_db()
marketing_db = MarketingDatabaseTools(db)
profile_manager = MarketingProfileManager(db)


# ==================== Profile Search Tools ====================

def tool_search_profile_by_name(
    profile_name: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for a marketing profile by name for a specific user.

    This tool helps find the profile_id when you only have the profile name.
    Use this BEFORE calling other tools that require profile_id.

    Args:
        profile_name: Name of the profile to search for (case-insensitive partial match)
        user_id: Optional UUID of the user (defaults to current session user)

    Returns:
        Dictionary with:
        - success (bool): True if found
        - profiles (list): List of matching profiles with id, name, type
        - message (str): Status message

    Example:
        tool_search_profile_by_name(profile_name="Shahzeb")
        Returns: {"success": True, "profiles": [{"profile_id": "...", "profile_name": "Shahzeb Naeem", ...}]}
    """
    try:
        # Get user_id from session if not provided
        if user_id is None:
            print(f"🔍 [PROFILE SEARCH] user_id not provided, attempting to get from session...")
            user_id = get_current_user_id()
            if user_id is None:
                print(f"❌ [PROFILE SEARCH] Failed to get user_id from session")
                return {
                    'success': False,
                    'profiles': [],
                    'error': 'No user_id provided and unable to get from session',
                    'message': 'user_id is required. Please provide it or ensure you are in an active session.'
                }
            print(f"✅ [PROFILE SEARCH] Using user_id from session: {user_id}")
        else:
            print(f"✅ [PROFILE SEARCH] user_id provided as parameter: {user_id}")

        # Get all profiles for user
        profiles = profile_manager.get_user_profiles(user_id)
        print(f"🔍 [PROFILE SEARCH] Found {len(profiles) if profiles else 0} total profiles for user {user_id}")

        if profiles:
            print(f"📋 [PROFILE SEARCH] Profile names: {[p.get('profile_name', 'UNNAMED') for p in profiles]}")

        if not profiles:
            return {
                'success': False,
                'profiles': [],
                'message': f"No profiles found for user_id {user_id}. Please create a profile first."
            }

        # Search for matching profiles (case-insensitive)
        search_term = profile_name.lower()
        print(f"🔎 [PROFILE SEARCH] Searching for '{search_term}' (case-insensitive)")

        matching_profiles = [
            {
                'profile_id': str(p['profile_id']),
                'profile_name': p['profile_name'],
                'profile_type': p['profile_type'],
                'industry': p.get('industry'),
                'is_default': p.get('is_default', False)
            }
            for p in profiles
            if search_term in p['profile_name'].lower()
        ]

        print(f"✅ [PROFILE SEARCH] Found {len(matching_profiles)} matching profile(s)")

        if matching_profiles:
            return {
                'success': True,
                'profiles': matching_profiles,
                'message': f"Found {len(matching_profiles)} matching profile(s). Use the profile_id for other operations.",
                'total_user_profiles': len(profiles)
            }
        else:
            # Return all profiles if no match
            all_profiles = [
                {
                    'profile_id': str(p['profile_id']),
                    'profile_name': p['profile_name'],
                    'profile_type': p['profile_type'],
                    'is_default': p.get('is_default', False)
                }
                for p in profiles
            ]
            return {
                'success': False,
                'profiles': all_profiles,
                'message': f"No profiles matching '{profile_name}'. Here are all {len(profiles)} profiles for this user."
            }

    except Exception as e:
        return {
            'success': False,
            'profiles': [],
            'error': str(e),
            'message': f"Error searching profiles: {str(e)}"
        }


# ==================== Strategy Management Tools ====================

def tool_create_marketing_strategy(
    user_id: str,
    profile_id: str,
    strategy_name: str,
    strategy_period: str,
    target_goals: Dict[str, Any],
    target_audience: str,
    content_themes: List[Dict[str, Any]],
    posting_frequency: Dict[str, str],
    tone_guidelines: str,
    messaging_pillars: List[str],
    competitor_insights: Optional[str] = None,
    market_positioning: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive marketing strategy for a profile.

    **IMPORTANT**: Only call this AFTER getting explicit user confirmation.

    Args:
        user_id: UUID of the user
        profile_id: UUID of the marketing profile
        strategy_name: Name of the strategy (e.g., "Q1 2024 Thought Leadership")
        strategy_period: Time period (e.g., "Q1 2024", "Jan-Mar 2024")
        target_goals: Dictionary of goals
            Example: {"reach": 10000, "engagement_rate": 5, "leads": 50, "thought_leadership": true}
        target_audience: Description of target audience
            Example: "Tech executives and AI decision-makers"
        content_themes: List of theme objects with name, description, and priority
            Example: [{"name": "AI Innovation", "description": "Latest AI trends", "priority": 1}]
        posting_frequency: Dictionary of platform frequencies
            Example: {"linkedin": "3x/week", "twitter": "daily"}
        tone_guidelines: Guidelines for tone and voice
            Example: "Professional yet approachable, data-driven storytelling"
        messaging_pillars: List of key messages to reinforce
            Example: ["Deep AI expertise", "Practical insights", "Future-focused"]
        competitor_insights: Optional competitive analysis
        market_positioning: Optional differentiation strategy

    Returns:
        Dictionary with:
        - success (bool): True if created successfully
        - strategy_id (str): UUID of created strategy
        - message (str): Confirmation message
        - error (str): Error message if failed
    """
    try:
        strategy_id = marketing_db.create_strategy(
            user_id=user_id,
            profile_id=profile_id,
            strategy_name=strategy_name,
            strategy_period=strategy_period,
            target_goals=target_goals,
            target_audience=target_audience,
            content_themes=content_themes,
            posting_frequency=posting_frequency,
            tone_guidelines=tone_guidelines,
            messaging_pillars=messaging_pillars,
            competitor_insights=competitor_insights,
            market_positioning=market_positioning,
            status='active'  # New strategies are active by default
        )

        return {
            'success': True,
            'strategy_id': strategy_id,
            'message': f"Marketing strategy '{strategy_name}' created successfully and set to active status.",
            'themes_count': len(content_themes),
            'period': strategy_period
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to create marketing strategy: {str(e)}"
        }


def tool_get_marketing_strategy(
    strategy_id: Optional[str] = None,
    profile_id: Optional[str] = None,
    get_active: bool = False
) -> Dict[str, Any]:
    """
    Retrieve a marketing strategy.

    Args:
        strategy_id: UUID of specific strategy (optional)
        profile_id: UUID of profile to get active strategy for (optional)
        get_active: If True with profile_id, get the active strategy

    Returns:
        Dictionary with:
        - success (bool): True if found
        - strategy (dict): Strategy data
        - message (str): Info message
        - error (str): Error message if failed
    """
    try:
        if strategy_id:
            strategy = marketing_db.get_strategy(strategy_id)
        elif profile_id and get_active:
            strategy = marketing_db.get_active_strategy(profile_id)
        else:
            return {
                'success': False,
                'error': 'Must provide either strategy_id or (profile_id + get_active=True)',
                'message': 'Invalid parameters'
            }

        if not strategy:
            return {
                'success': False,
                'message': 'No strategy found with given parameters',
                'strategy': None
            }

        return {
            'success': True,
            'strategy': strategy,
            'message': f"Retrieved strategy: {strategy.get('strategy_name')}"
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to retrieve strategy: {str(e)}"
        }


def tool_update_marketing_strategy(
    strategy_id: str,
    **updates
) -> Dict[str, Any]:
    """
    Update an existing marketing strategy.

    **IMPORTANT**: Only call this AFTER getting explicit user confirmation.

    Args:
        strategy_id: UUID of the strategy to update
        **updates: Fields to update (strategy_name, target_goals, content_themes, etc.)

    Returns:
        Dictionary with success status and message
    """
    try:
        success = marketing_db.update_strategy(strategy_id, **updates)

        if success:
            return {
                'success': True,
                'strategy_id': strategy_id,
                'message': 'Marketing strategy updated successfully',
                'updated_fields': list(updates.keys())
            }
        else:
            return {
                'success': False,
                'message': 'No valid fields to update or strategy not found'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to update strategy: {str(e)}"
        }


# ==================== Profile Management Tools ====================

def tool_create_marketing_profile(
    user_id: str,
    profile_type: str,
    profile_name: str,
    relationship_type: str = 'standalone_individual',
    brand_voice: Optional[str] = None,
    industry: Optional[str] = None,
    target_audience: Optional[str] = None,
    content_themes: Optional[List[str]] = None,
    role_title: Optional[str] = None,
    expertise_areas: Optional[List[str]] = None,
    is_default: bool = False
) -> Dict[str, Any]:
    """
    Create a new marketing profile (individual, company, or employee).

    **IMPORTANT**: Only call this AFTER getting explicit user confirmation.

    Args:
        user_id: UUID of the user
        profile_type: 'personal' or 'company'
        profile_name: Display name for the profile
        relationship_type: 'standalone_individual', 'standalone_company', or 'company_employee'
        brand_voice: Description of brand voice
        industry: Industry/sector
        target_audience: Description of target audience
        content_themes: List of content themes
        role_title: Role title (for personal profiles)
        expertise_areas: List of expertise areas (for personal profiles)
        is_default: Whether this is the default profile

    Returns:
        Dictionary with success status and profile_id
    """
    try:
        profile_id = profile_manager.create_profile(
            user_id=user_id,
            profile_type=profile_type,
            profile_name=profile_name,
            relationship_type=relationship_type,
            brand_voice=brand_voice,
            industry=industry,
            target_audience=target_audience,
            content_themes=content_themes,
            role_title=role_title,
            expertise_areas=expertise_areas,
            is_default=is_default
        )

        return {
            'success': True,
            'profile_id': profile_id,
            'profile_name': profile_name,
            'profile_type': profile_type,
            'relationship_type': relationship_type,
            'message': f"Marketing profile '{profile_name}' created successfully"
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to create profile: {str(e)}"
        }


def tool_link_employee_to_company(
    employee_profile_id: str,
    company_profile_id: str,
    employee_role: str
) -> Dict[str, Any]:
    """
    Link an employee profile to a company profile.

    **IMPORTANT**: Only call this AFTER getting explicit user confirmation.

    Args:
        employee_profile_id: UUID of the employee profile
        company_profile_id: UUID of the company profile
        employee_role: Role title (e.g., "CEO", "CMO", "Marketing Director")

    Returns:
        Dictionary with success status and message
    """
    try:
        success = marketing_db.link_employee_to_company(
            employee_profile_id=employee_profile_id,
            company_profile_id=company_profile_id,
            employee_role=employee_role
        )

        if success:
            return {
                'success': True,
                'employee_profile_id': employee_profile_id,
                'company_profile_id': company_profile_id,
                'employee_role': employee_role,
                'message': f"Successfully linked employee as {employee_role} to company profile"
            }
        else:
            return {
                'success': False,
                'message': 'Failed to link employee to company'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to link employee: {str(e)}"
        }


# ==================== Content Planning Tools ====================

def tool_plan_content_calendar(
    user_id: str,
    profile_id: str,
    calendar_entries: List[Dict[str, Any]],
    strategy_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create multiple content calendar entries at once.

    **IMPORTANT**: Only call this AFTER getting explicit user confirmation.

    Args:
        user_id: UUID of the user
        profile_id: UUID of the profile
        calendar_entries: List of entry dictionaries, each with:
            - scheduled_date (str): Date in YYYY-MM-DD format
            - topic (str): Topic/title of the content
            - content_type (str): Type of content (default: 'linkedin_post')
            - theme (str, optional): Theme from strategy
            - draft_text (str, optional): Draft content
        strategy_id: Optional UUID of related strategy

    Example:
        calendar_entries = [
            {
                "scheduled_date": "2024-02-15",
                "topic": "AI trends in healthcare",
                "content_type": "linkedin_post",
                "theme": "AI Innovation"
            },
            {
                "scheduled_date": "2024-02-18",
                "topic": "Leadership lessons from AI implementation",
                "content_type": "thought_leadership",
                "theme": "Leadership Insights"
            }
        ]

    Returns:
        Dictionary with:
        - success (bool): True if all created successfully
        - created_count (int): Number of entries created
        - calendar_ids (list): List of created calendar entry IDs
        - message (str): Confirmation message
        - error (str): Error message if failed
    """
    try:
        created_ids = []

        for entry in calendar_entries:
            # Parse date string to date object
            scheduled_date = datetime.strptime(entry['scheduled_date'], '%Y-%m-%d').date()

            calendar_id = marketing_db.add_calendar_entry(
                user_id=user_id,
                profile_id=profile_id,
                scheduled_date=scheduled_date,
                topic=entry['topic'],
                content_type=entry.get('content_type', 'linkedin_post'),
                strategy_id=strategy_id,
                theme=entry.get('theme'),
                draft_text=entry.get('draft_text'),
                status='planned'
            )
            created_ids.append(calendar_id)

        return {
            'success': True,
            'created_count': len(created_ids),
            'calendar_ids': created_ids,
            'message': f"Successfully created {len(created_ids)} content calendar entries"
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to create content calendar: {str(e)}",
            'created_count': len(created_ids) if 'created_ids' in locals() else 0
        }


def tool_suggest_next_post(
    profile_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Suggest what to post next based on strategy, calendar, and recent post performance.

    This is a READ-ONLY tool - no confirmation needed.

    Args:
        profile_id: UUID of the profile
        user_id: UUID of the user

    Returns:
        Dictionary with:
        - success (bool): True if suggestion generated
        - suggestion (dict): Suggested post with topic, theme, type, reasoning
        - upcoming_calendar (list): Upcoming scheduled posts
        - recent_performance (dict): Performance insights
        - message (str): Info message
    """
    try:
        # Get active strategy
        strategy = marketing_db.get_active_strategy(profile_id)

        # Get upcoming content
        upcoming = marketing_db.get_upcoming_content(profile_id, days_ahead=7)

        # Get recent post performance
        performance = marketing_db.get_post_performance_by_theme(profile_id, limit=10)

        # Generate suggestion based on data
        suggestion = {
            'topic': None,
            'theme': None,
            'content_type': 'linkedin_post',
            'reasoning': []
        }

        if strategy:
            themes = strategy.get('content_themes', [])
            if themes:
                # Suggest highest priority theme that hasn't been posted recently
                upcoming_themes = [entry.get('theme') for entry in upcoming if entry.get('theme')]

                # Find highest priority theme not in upcoming
                for theme in sorted(themes, key=lambda x: x.get('priority', 999)):
                    theme_name = theme.get('name')
                    if theme_name not in upcoming_themes:
                        suggestion['theme'] = theme_name
                        suggestion['reasoning'].append(f"Theme '{theme_name}' is high priority and not recently scheduled")
                        break

            # Suggest posting frequency
            frequency = strategy.get('posting_frequency', {})
            suggestion['reasoning'].append(f"Strategy recommends posting {frequency.get('linkedin', '2-3x/week')}")

        # Performance-based recommendations
        if performance and performance.get('themes'):
            top_theme = performance['themes'][0]
            if top_theme.get('avg_rating', 0) >= 4:
                suggestion['reasoning'].append(
                    f"Theme '{top_theme['theme']}' performed well (avg rating: {top_theme['avg_rating']:.1f})"
                )

        # Default suggestion if no strategy
        if not suggestion['theme']:
            suggestion['theme'] = "Industry insights"
            suggestion['reasoning'].append("Consider posting industry insights or thought leadership")

        suggestion['topic'] = f"Share insights about {suggestion['theme']}"

        return {
            'success': True,
            'suggestion': suggestion,
            'upcoming_calendar': upcoming,
            'recent_performance': performance,
            'has_strategy': strategy is not None,
            'message': 'Content suggestion generated based on strategy and performance data'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to generate suggestion: {str(e)}"
        }


# ==================== Cross-Profile Campaign Tools ====================

def tool_create_cross_profile_campaign(
    user_id: str,
    campaign_name: str,
    campaign_theme: str,
    primary_profile_id: str,
    participating_profile_ids: List[str],
    key_messages: List[str],
    coordination_notes: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a cross-profile campaign to coordinate messaging across multiple profiles.

    **IMPORTANT**: Only call this AFTER getting explicit user confirmation.

    Args:
        user_id: UUID of the user
        campaign_name: Name of the campaign (e.g., "Product Launch 2024")
        campaign_theme: Theme/topic of the campaign
        primary_profile_id: UUID of the lead profile (e.g., company page)
        participating_profile_ids: List of profile UUIDs participating
        key_messages: List of key messages to communicate
        coordination_notes: Notes on timing and sequencing
            Example: "CEO posts Mon 9am, Company page Tue 10am, CMO Wed 2pm"
        start_date: Campaign start date (YYYY-MM-DD format, optional)
        end_date: Campaign end date (YYYY-MM-DD format, optional)

    Returns:
        Dictionary with:
        - success (bool): True if created successfully
        - campaign_id (str): UUID of created campaign
        - message (str): Confirmation message
        - error (str): Error message if failed
    """
    try:
        # Parse dates if provided
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

        campaign_id = marketing_db.create_campaign(
            user_id=user_id,
            campaign_name=campaign_name,
            campaign_theme=campaign_theme,
            primary_profile_id=primary_profile_id,
            participating_profiles=participating_profile_ids,
            key_messages=key_messages,
            coordination_notes=coordination_notes,
            start_date=start_date_obj,
            end_date=end_date_obj,
            status='planned'
        )

        return {
            'success': True,
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'participating_count': len(participating_profile_ids),
            'message': f"Campaign '{campaign_name}' created successfully with {len(participating_profile_ids)} participating profiles"
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to create campaign: {str(e)}"
        }
