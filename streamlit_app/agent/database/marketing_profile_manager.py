"""
Marketing Profile Manager
Handles CRUD operations for marketing profiles and generated LinkedIn posts
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
import uuid
from psycopg2.extras import Json
from datetime import datetime

from agent.database.db_manager import DatabaseManager


class MarketingProfileManager:
    """Manages marketing profiles and generated posts in the database"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # ==================== Marketing Profiles ====================

    def create_profile(
        self,
        user_id: str,
        profile_type: str,
        profile_name: str,
        brand_voice: Optional[str] = None,
        industry: Optional[str] = None,
        target_audience: Optional[str] = None,
        content_themes: Optional[List[str]] = None,
        default_tone: str = "professional",
        image_style_preference: str = "professional",
        is_default: bool = False,
        **kwargs
    ) -> str:
        """
        Create a new marketing profile

        Args:
            user_id: UUID of the user
            profile_type: 'personal' or 'company'
            profile_name: Display name for the profile
            brand_voice: Description of brand voice
            industry: Industry/sector
            target_audience: Description of target audience
            content_themes: List of content themes
            default_tone: Default tone for posts
            image_style_preference: Default image style
            is_default: Whether this is the default profile
            **kwargs: Additional optional fields (brand_colors, company_size, role_title, etc.)

        Returns:
            profile_id (str): UUID of created profile
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                # Build dynamic field list based on kwargs
                fields = [
                    'user_id', 'profile_type', 'profile_name', 'brand_voice',
                    'industry', 'target_audience', 'content_themes',
                    'default_tone', 'image_style_preference', 'is_default'
                ]
                values = [
                    user_id, profile_type, profile_name, brand_voice,
                    industry, target_audience, content_themes,
                    default_tone, image_style_preference, is_default
                ]

                # Add optional fields from kwargs
                optional_fields = [
                    'brand_colors', 'company_size', 'logo_url', 'typical_post_style',
                    'example_posts', 'role_title', 'expertise_areas', 'personal_bio',
                    'avoid_topics', 'profile_metadata', 'relationship_type', 'company_id', 'employee_role'
                ]

                for field in optional_fields:
                    if field in kwargs and kwargs[field] is not None:
                        fields.append(field)
                        # Wrap JSONB fields in Json() for proper serialization
                        if field in ['brand_colors', 'example_posts', 'profile_metadata']:
                            values.append(Json(kwargs[field]))
                        else:
                            values.append(kwargs[field])

                # Build SQL
                placeholders = ', '.join(['%s'] * len(fields))
                field_names = ', '.join(fields)

                sql = f"""
                    INSERT INTO marketing_profiles ({field_names})
                    VALUES ({placeholders})
                    RETURNING profile_id
                """

                cursor.execute(sql, values)
                profile_id = cursor.fetchone()[0]
                conn.commit()

                print(f"✅ Created marketing profile: {profile_name} ({profile_id})")
                return str(profile_id)

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get a marketing profile by ID"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        profile_id, user_id, profile_type, profile_name, is_default,
                        brand_colors, brand_voice, industry, company_size, logo_url,
                        target_audience, content_themes, typical_post_style, example_posts,
                        role_title, expertise_areas, personal_bio,
                        default_tone, image_style_preference, avoid_topics,
                        profile_metadata, created_at, updated_at
                    FROM marketing_profiles
                    WHERE profile_id = %s
                """, (profile_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_profile_dict(cursor, row)

    def get_user_profiles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all marketing profiles for a user"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        profile_id, user_id, profile_type, profile_name, is_default,
                        brand_colors, brand_voice, industry, company_size, logo_url,
                        target_audience, content_themes, typical_post_style, example_posts,
                        role_title, expertise_areas, personal_bio,
                        default_tone, image_style_preference, avoid_topics,
                        profile_metadata, created_at, updated_at
                    FROM marketing_profiles
                    WHERE user_id = %s
                    ORDER BY is_default DESC, created_at DESC
                """, (user_id,))

                rows = cursor.fetchall()
                return [self._row_to_profile_dict(cursor, row) for row in rows]

    def get_default_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's default marketing profile"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        profile_id, user_id, profile_type, profile_name, is_default,
                        brand_colors, brand_voice, industry, company_size, logo_url,
                        target_audience, content_themes, typical_post_style, example_posts,
                        role_title, expertise_areas, personal_bio,
                        default_tone, image_style_preference, avoid_topics,
                        profile_metadata, created_at, updated_at
                    FROM marketing_profiles
                    WHERE user_id = %s AND is_default = TRUE
                    LIMIT 1
                """, (user_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_profile_dict(cursor, row)

    def update_profile(self, profile_id: str, **kwargs) -> bool:
        """
        Update a marketing profile

        Args:
            profile_id: UUID of profile to update
            **kwargs: Fields to update

        Returns:
            bool: True if updated successfully
        """
        if not kwargs:
            return False

        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                # Build SET clause dynamically
                set_clauses = []
                values = []

                for field, value in kwargs.items():
                    set_clauses.append(f"{field} = %s")
                    # Wrap JSONB fields in Json()
                    if field in ['brand_colors', 'example_posts', 'profile_metadata']:
                        values.append(Json(value))
                    else:
                        values.append(value)

                values.append(profile_id)

                sql = f"""
                    UPDATE marketing_profiles
                    SET {', '.join(set_clauses)}
                    WHERE profile_id = %s
                """

                cursor.execute(sql, values)
                rows_affected = cursor.rowcount
                conn.commit()

                return rows_affected > 0

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a marketing profile"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM marketing_profiles
                    WHERE profile_id = %s
                """, (profile_id,))

                rows_affected = cursor.rowcount
                conn.commit()

                return rows_affected > 0

    def set_default_profile(self, user_id: str, profile_id: str) -> bool:
        """Set a profile as the default for a user (unsets others)"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                # First unset all defaults for this user
                cursor.execute("""
                    UPDATE marketing_profiles
                    SET is_default = FALSE
                    WHERE user_id = %s
                """, (user_id,))

                # Then set the specified profile as default
                cursor.execute("""
                    UPDATE marketing_profiles
                    SET is_default = TRUE
                    WHERE profile_id = %s AND user_id = %s
                """, (profile_id, user_id))

                rows_affected = cursor.rowcount
                conn.commit()

                return rows_affected > 0

    # ==================== Generated LinkedIn Posts ====================

    def save_generated_post(
        self,
        user_id: str,
        post_topic: str,
        generated_text: str,
        profile_id: Optional[str] = None,
        session_id: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_prompt: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        post_type: Optional[str] = None,
        tone_used: Optional[str] = None,
        image_style_used: Optional[str] = None,
        gemini_reasoning: Optional[str] = None
    ) -> str:
        """
        Save a generated LinkedIn post to the database

        Returns:
            post_id (str): UUID of created post
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO generated_linkedin_posts (
                        user_id, profile_id, session_id, post_topic, generated_text,
                        image_bytes, image_prompt, hashtags, post_type,
                        tone_used, image_style_used, gemini_reasoning
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING post_id
                """, (
                    user_id, profile_id, session_id, post_topic, generated_text,
                    image_bytes, image_prompt, hashtags, post_type,
                    tone_used, image_style_used, gemini_reasoning
                ))

                post_id = cursor.fetchone()[0]
                conn.commit()

                print(f"✅ Saved generated post: {post_id}")
                return str(post_id)

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get a generated post by ID"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        post_id, user_id, profile_id, session_id,
                        post_topic, generated_text, image_bytes, image_prompt, hashtags,
                        post_type, tone_used, image_style_used, gemini_reasoning,
                        user_rating, was_posted, user_edits, performance_notes,
                        created_at
                    FROM generated_linkedin_posts
                    WHERE post_id = %s
                """, (post_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_post_dict(cursor, row)

    def get_user_posts(
        self,
        user_id: str,
        profile_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get generated posts for a user, optionally filtered by profile"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                if profile_id:
                    cursor.execute("""
                        SELECT
                            post_id, user_id, profile_id, session_id,
                            post_topic, generated_text, image_bytes, image_prompt, hashtags,
                            post_type, tone_used, image_style_used, gemini_reasoning,
                            user_rating, was_posted, user_edits, performance_notes,
                            created_at
                        FROM generated_linkedin_posts
                        WHERE user_id = %s AND profile_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, profile_id, limit))
                else:
                    cursor.execute("""
                        SELECT
                            post_id, user_id, profile_id, session_id,
                            post_topic, generated_text, image_bytes, image_prompt, hashtags,
                            post_type, tone_used, image_style_used, gemini_reasoning,
                            user_rating, was_posted, user_edits, performance_notes,
                            created_at
                        FROM generated_linkedin_posts
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, limit))

                rows = cursor.fetchall()
                return [self._row_to_post_dict(cursor, row) for row in rows]

    def update_post_feedback(
        self,
        post_id: str,
        user_rating: Optional[int] = None,
        was_posted: Optional[bool] = None,
        user_edits: Optional[str] = None,
        performance_notes: Optional[str] = None
    ) -> bool:
        """Update user feedback for a generated post"""
        updates = {}
        if user_rating is not None:
            updates['user_rating'] = user_rating
        if was_posted is not None:
            updates['was_posted'] = was_posted
        if user_edits is not None:
            updates['user_edits'] = user_edits
        if performance_notes is not None:
            updates['performance_notes'] = performance_notes

        if not updates:
            return False

        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                set_clauses = [f"{k} = %s" for k in updates.keys()]
                values = list(updates.values()) + [post_id]

                sql = f"""
                    UPDATE generated_linkedin_posts
                    SET {', '.join(set_clauses)}
                    WHERE post_id = %s
                """

                cursor.execute(sql, values)
                rows_affected = cursor.rowcount
                conn.commit()

                return rows_affected > 0

    # ==================== Helper Methods ====================

    def _row_to_profile_dict(self, cursor, row) -> Dict[str, Any]:
        """Convert database row to profile dictionary"""
        columns = [desc[0] for desc in cursor.description]
        profile = dict(zip(columns, row))

        # Convert UUID to string for JSON serialization
        if 'profile_id' in profile and profile['profile_id']:
            profile['profile_id'] = str(profile['profile_id'])
        if 'user_id' in profile and profile['user_id']:
            profile['user_id'] = str(profile['user_id'])

        return profile

    def _row_to_post_dict(self, cursor, row) -> Dict[str, Any]:
        """Convert database row to post dictionary"""
        columns = [desc[0] for desc in cursor.description]
        post = dict(zip(columns, row))

        # Convert UUIDs to strings
        for key in ['post_id', 'user_id', 'profile_id', 'session_id']:
            if key in post and post[key]:
                post[key] = str(post[key])

        return post

    # ==================== Statistics ====================

    def get_profile_stats(self, profile_id: str) -> Dict[str, Any]:
        """Get statistics for a profile (post count, etc.)"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_posts,
                        COUNT(*) FILTER (WHERE was_posted = TRUE) as posted_count,
                        AVG(user_rating) FILTER (WHERE user_rating IS NOT NULL) as avg_rating
                    FROM generated_linkedin_posts
                    WHERE profile_id = %s
                """, (profile_id,))

                row = cursor.fetchone()
                return {
                    'total_posts': row[0] or 0,
                    'posted_count': row[1] or 0,
                    'avg_rating': float(row[2]) if row[2] else None
                }
