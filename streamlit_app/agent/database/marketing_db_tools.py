"""
Marketing Database Tools
Handles CRUD operations for marketing strategies, content calendars, and campaigns
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
import uuid
from psycopg2.extras import Json
from datetime import datetime, date

from agent.database.db_manager import DatabaseManager


class MarketingDatabaseTools:
    """Manages marketing strategies, content calendars, and campaigns in the database"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # ==================== Marketing Strategies ====================

    def create_strategy(
        self,
        user_id: str,
        profile_id: str,
        strategy_name: str,
        strategy_period: Optional[str] = None,
        target_goals: Optional[Dict] = None,
        target_audience: Optional[str] = None,
        content_themes: Optional[List[Dict]] = None,
        posting_frequency: Optional[Dict] = None,
        tone_guidelines: Optional[str] = None,
        messaging_pillars: Optional[List[str]] = None,
        competitor_insights: Optional[str] = None,
        market_positioning: Optional[str] = None,
        status: str = 'draft'
    ) -> str:
        """
        Create a new marketing strategy

        Args:
            user_id: UUID of the user
            profile_id: UUID of the profile this strategy belongs to
            strategy_name: Name of the strategy
            strategy_period: Time period (e.g., "Q1 2024")
            target_goals: Dictionary of goals (e.g., {"reach": 10000, "engagement_rate": 5})
            target_audience: Description of target audience
            content_themes: List of theme objects (e.g., [{"name": "AI Innovation", "priority": 1}])
            posting_frequency: Dictionary of frequencies (e.g., {"linkedin": "3x/week"})
            tone_guidelines: Guidelines for tone and voice
            messaging_pillars: Key messages to reinforce
            competitor_insights: Competitive analysis
            market_positioning: How to differentiate
            status: 'draft', 'active', or 'archived'

        Returns:
            strategy_id (str): UUID of created strategy
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO marketing_strategies (
                        user_id, profile_id, strategy_name, strategy_period,
                        target_goals, target_audience, content_themes, posting_frequency,
                        tone_guidelines, messaging_pillars, competitor_insights,
                        market_positioning, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING strategy_id
                """

                cursor.execute(sql, (
                    user_id, profile_id, strategy_name, strategy_period,
                    Json(target_goals or {}), target_audience,
                    Json(content_themes or []), Json(posting_frequency or {}),
                    tone_guidelines, Json(messaging_pillars or []),
                    competitor_insights, market_positioning, status
                ))

                strategy_id = cursor.fetchone()[0]
                conn.commit()

                print(f"✅ Created marketing strategy: {strategy_name} ({strategy_id})")
                return str(strategy_id)

    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """
        Retrieve a marketing strategy by ID

        Args:
            strategy_id: UUID of the strategy

        Returns:
            Dictionary with strategy data or None if not found
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        strategy_id, user_id, profile_id, strategy_name, strategy_period,
                        target_goals, target_audience, content_themes, posting_frequency,
                        tone_guidelines, messaging_pillars, competitor_insights,
                        market_positioning, status, created_at, updated_at
                    FROM marketing_strategies
                    WHERE strategy_id = %s
                """
                cursor.execute(sql, (strategy_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    'strategy_id': str(row[0]),
                    'user_id': str(row[1]),
                    'profile_id': str(row[2]),
                    'strategy_name': row[3],
                    'strategy_period': row[4],
                    'target_goals': row[5],
                    'target_audience': row[6],
                    'content_themes': row[7],
                    'posting_frequency': row[8],
                    'tone_guidelines': row[9],
                    'messaging_pillars': row[10],
                    'competitor_insights': row[11],
                    'market_positioning': row[12],
                    'status': row[13],
                    'created_at': row[14].isoformat() if row[14] else None,
                    'updated_at': row[15].isoformat() if row[15] else None
                }

    def get_active_strategy(self, profile_id: str) -> Optional[Dict]:
        """
        Get the active strategy for a profile

        Args:
            profile_id: UUID of the profile

        Returns:
            Dictionary with strategy data or None if no active strategy
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        strategy_id, user_id, profile_id, strategy_name, strategy_period,
                        target_goals, target_audience, content_themes, posting_frequency,
                        tone_guidelines, messaging_pillars, competitor_insights,
                        market_positioning, status, created_at, updated_at
                    FROM marketing_strategies
                    WHERE profile_id = %s AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                cursor.execute(sql, (profile_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    'strategy_id': str(row[0]),
                    'user_id': str(row[1]),
                    'profile_id': str(row[2]),
                    'strategy_name': row[3],
                    'strategy_period': row[4],
                    'target_goals': row[5],
                    'target_audience': row[6],
                    'content_themes': row[7],
                    'posting_frequency': row[8],
                    'tone_guidelines': row[9],
                    'messaging_pillars': row[10],
                    'competitor_insights': row[11],
                    'market_positioning': row[12],
                    'status': row[13],
                    'created_at': row[14].isoformat() if row[14] else None,
                    'updated_at': row[15].isoformat() if row[15] else None
                }

    def update_strategy(
        self,
        strategy_id: str,
        **kwargs
    ) -> bool:
        """
        Update a marketing strategy

        Args:
            strategy_id: UUID of the strategy to update
            **kwargs: Fields to update (strategy_name, target_goals, content_themes, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            return False

        allowed_fields = [
            'strategy_name', 'strategy_period', 'target_goals', 'target_audience',
            'content_themes', 'posting_frequency', 'tone_guidelines', 'messaging_pillars',
            'competitor_insights', 'market_positioning', 'status'
        ]

        # Build SET clause dynamically
        set_clauses = []
        values = []

        for field, value in kwargs.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = %s")
                # Wrap JSONB fields in Json() for proper serialization
                if field in ['target_goals', 'content_themes', 'posting_frequency', 'messaging_pillars']:
                    values.append(Json(value))
                else:
                    values.append(value)

        if not set_clauses:
            return False

        values.append(strategy_id)

        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = f"""
                    UPDATE marketing_strategies
                    SET {', '.join(set_clauses)}
                    WHERE strategy_id = %s
                """
                cursor.execute(sql, values)
                conn.commit()

                print(f"✅ Updated marketing strategy: {strategy_id}")
                return True

    def list_user_strategies(self, user_id: str) -> List[Dict]:
        """
        List all strategies for a user

        Args:
            user_id: UUID of the user

        Returns:
            List of strategy dictionaries
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        s.strategy_id, s.user_id, s.profile_id, s.strategy_name,
                        s.strategy_period, s.status, s.created_at,
                        p.profile_name
                    FROM marketing_strategies s
                    LEFT JOIN marketing_profiles p ON s.profile_id = p.profile_id
                    WHERE s.user_id = %s
                    ORDER BY s.created_at DESC
                """
                cursor.execute(sql, (user_id,))
                rows = cursor.fetchall()

                strategies = []
                for row in rows:
                    strategies.append({
                        'strategy_id': str(row[0]),
                        'user_id': str(row[1]),
                        'profile_id': str(row[2]),
                        'strategy_name': row[3],
                        'strategy_period': row[4],
                        'status': row[5],
                        'created_at': row[6].isoformat() if row[6] else None,
                        'profile_name': row[7]
                    })

                return strategies

    # ==================== Content Calendar ====================

    def add_calendar_entry(
        self,
        user_id: str,
        profile_id: str,
        scheduled_date: date,
        topic: str,
        content_type: str = 'linkedin_post',
        strategy_id: Optional[str] = None,
        theme: Optional[str] = None,
        draft_text: Optional[str] = None,
        status: str = 'planned'
    ) -> str:
        """
        Add an entry to the content calendar

        Args:
            user_id: UUID of the user
            profile_id: UUID of the profile
            scheduled_date: Date to publish
            topic: Topic/title of the content
            content_type: Type of content ('linkedin_post', 'article', etc.)
            strategy_id: Optional UUID of related strategy
            theme: Optional theme from strategy
            draft_text: Optional draft content
            status: 'planned', 'drafted', 'posted', or 'skipped'

        Returns:
            calendar_id (str): UUID of created calendar entry
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO content_calendar (
                        user_id, profile_id, scheduled_date, topic, content_type,
                        strategy_id, theme, draft_text, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING calendar_id
                """

                cursor.execute(sql, (
                    user_id, profile_id, scheduled_date, topic, content_type,
                    strategy_id, theme, draft_text, status
                ))

                calendar_id = cursor.fetchone()[0]
                conn.commit()

                print(f"✅ Added calendar entry: {topic} on {scheduled_date} ({calendar_id})")
                return str(calendar_id)

    def get_upcoming_content(
        self,
        profile_id: str,
        days_ahead: int = 7
    ) -> List[Dict]:
        """
        Get upcoming calendar entries for a profile

        Args:
            profile_id: UUID of the profile
            days_ahead: Number of days to look ahead (default 7)

        Returns:
            List of calendar entry dictionaries
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        calendar_id, scheduled_date, topic, content_type,
                        status, theme, draft_text
                    FROM content_calendar
                    WHERE profile_id = %s
                      AND scheduled_date >= CURRENT_DATE
                      AND scheduled_date <= CURRENT_DATE + %s
                    ORDER BY scheduled_date ASC
                """
                cursor.execute(sql, (profile_id, days_ahead))
                rows = cursor.fetchall()

                entries = []
                for row in rows:
                    entries.append({
                        'calendar_id': str(row[0]),
                        'scheduled_date': row[1].isoformat() if row[1] else None,
                        'topic': row[2],
                        'content_type': row[3],
                        'status': row[4],
                        'theme': row[5],
                        'draft_text': row[6]
                    })

                return entries

    def update_calendar_entry(
        self,
        calendar_id: str,
        **kwargs
    ) -> bool:
        """
        Update a calendar entry

        Args:
            calendar_id: UUID of the calendar entry
            **kwargs: Fields to update (status, draft_text, final_post_id, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            return False

        allowed_fields = [
            'scheduled_date', 'topic', 'content_type', 'theme', 'status',
            'draft_text', 'final_post_id', 'performance_notes'
        ]

        # Build SET clause dynamically
        set_clauses = []
        values = []

        for field, value in kwargs.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = %s")
                values.append(value)

        if not set_clauses:
            return False

        values.append(calendar_id)

        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = f"""
                    UPDATE content_calendar
                    SET {', '.join(set_clauses)}
                    WHERE calendar_id = %s
                """
                cursor.execute(sql, values)
                conn.commit()

                print(f"✅ Updated calendar entry: {calendar_id}")
                return True

    # ==================== Cross-Profile Campaigns ====================

    def create_campaign(
        self,
        user_id: str,
        campaign_name: str,
        campaign_theme: str,
        primary_profile_id: str,
        participating_profiles: List[str],
        key_messages: Optional[List[str]] = None,
        coordination_notes: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: str = 'planned'
    ) -> str:
        """
        Create a cross-profile campaign

        Args:
            user_id: UUID of the user
            campaign_name: Name of the campaign
            campaign_theme: Theme/topic of the campaign
            primary_profile_id: UUID of the lead profile
            participating_profiles: List of profile UUIDs participating
            key_messages: List of key messages to communicate
            coordination_notes: Notes on timing and coordination
            start_date: Campaign start date
            end_date: Campaign end date
            status: 'planned', 'active', 'completed', or 'cancelled'

        Returns:
            campaign_id (str): UUID of created campaign
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO cross_profile_campaigns (
                        user_id, campaign_name, campaign_theme, primary_profile_id,
                        participating_profiles, key_messages, coordination_notes,
                        start_date, end_date, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING campaign_id
                """

                cursor.execute(sql, (
                    user_id, campaign_name, campaign_theme, primary_profile_id,
                    participating_profiles, Json(key_messages or []),
                    coordination_notes, start_date, end_date, status
                ))

                campaign_id = cursor.fetchone()[0]
                conn.commit()

                print(f"✅ Created campaign: {campaign_name} ({campaign_id})")
                return str(campaign_id)

    def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        """
        Retrieve a campaign by ID

        Args:
            campaign_id: UUID of the campaign

        Returns:
            Dictionary with campaign data or None if not found
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        campaign_id, user_id, campaign_name, campaign_theme,
                        primary_profile_id, participating_profiles, key_messages,
                        coordination_notes, start_date, end_date, status,
                        created_at, updated_at
                    FROM cross_profile_campaigns
                    WHERE campaign_id = %s
                """
                cursor.execute(sql, (campaign_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    'campaign_id': str(row[0]),
                    'user_id': str(row[1]),
                    'campaign_name': row[2],
                    'campaign_theme': row[3],
                    'primary_profile_id': str(row[4]),
                    'participating_profiles': [str(p) for p in row[5]],
                    'key_messages': row[6],
                    'coordination_notes': row[7],
                    'start_date': row[8].isoformat() if row[8] else None,
                    'end_date': row[9].isoformat() if row[9] else None,
                    'status': row[10],
                    'created_at': row[11].isoformat() if row[11] else None,
                    'updated_at': row[12].isoformat() if row[12] else None
                }

    def list_user_campaigns(self, user_id: str) -> List[Dict]:
        """
        List all campaigns for a user

        Args:
            user_id: UUID of the user

        Returns:
            List of campaign dictionaries
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        campaign_id, campaign_name, campaign_theme, status,
                        start_date, end_date, created_at
                    FROM cross_profile_campaigns
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(sql, (user_id,))
                rows = cursor.fetchall()

                campaigns = []
                for row in rows:
                    campaigns.append({
                        'campaign_id': str(row[0]),
                        'campaign_name': row[1],
                        'campaign_theme': row[2],
                        'status': row[3],
                        'start_date': row[4].isoformat() if row[4] else None,
                        'end_date': row[5].isoformat() if row[5] else None,
                        'created_at': row[6].isoformat() if row[6] else None
                    })

                return campaigns

    # ==================== Profile Hierarchy ====================

    def link_employee_to_company(
        self,
        employee_profile_id: str,
        company_profile_id: str,
        employee_role: str
    ) -> bool:
        """
        Link an employee profile to a company profile

        Args:
            employee_profile_id: UUID of the employee profile
            company_profile_id: UUID of the company profile
            employee_role: Role title (e.g., "CEO", "CMO")

        Returns:
            True if successful, False otherwise
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE marketing_profiles
                    SET company_id = %s,
                        employee_role = %s,
                        relationship_type = 'company_employee'
                    WHERE profile_id = %s
                """
                cursor.execute(sql, (company_profile_id, employee_role, employee_profile_id))
                conn.commit()

                print(f"✅ Linked employee profile {employee_profile_id} to company {company_profile_id}")
                return True

    def get_company_employees(self, company_profile_id: str) -> List[Dict]:
        """
        Get all employee profiles for a company

        Args:
            company_profile_id: UUID of the company profile

        Returns:
            List of employee profile dictionaries
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT profile_id, profile_name, employee_role, created_at
                    FROM marketing_profiles
                    WHERE company_id = %s
                      AND relationship_type = 'company_employee'
                    ORDER BY created_at ASC
                """
                cursor.execute(sql, (company_profile_id,))
                rows = cursor.fetchall()

                employees = []
                for row in rows:
                    employees.append({
                        'profile_id': str(row[0]),
                        'profile_name': row[1],
                        'employee_role': row[2],
                        'created_at': row[3].isoformat() if row[3] else None
                    })

                return employees

    # ==================== Performance Analytics ====================

    def get_post_performance_by_theme(
        self,
        profile_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze post performance by content theme

        Args:
            profile_id: UUID of the profile
            limit: Max posts to analyze

        Returns:
            Dictionary with performance insights by theme
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        c.theme,
                        COUNT(*) as post_count,
                        AVG(p.user_rating) as avg_rating,
                        COUNT(CASE WHEN p.was_posted = TRUE THEN 1 END) as posted_count
                    FROM content_calendar c
                    LEFT JOIN generated_linkedin_posts p ON c.final_post_id = p.post_id
                    WHERE c.profile_id = %s
                      AND c.theme IS NOT NULL
                      AND c.status = 'posted'
                    GROUP BY c.theme
                    ORDER BY avg_rating DESC, post_count DESC
                    LIMIT %s
                """
                cursor.execute(sql, (profile_id, limit))
                rows = cursor.fetchall()

                themes = []
                for row in rows:
                    themes.append({
                        'theme': row[0],
                        'post_count': row[1],
                        'avg_rating': float(row[2]) if row[2] else None,
                        'posted_count': row[3]
                    })

                return {
                    'profile_id': profile_id,
                    'themes': themes,
                    'analysis_date': datetime.now().isoformat()
                }
