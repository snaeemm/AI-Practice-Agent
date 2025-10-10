"""
Singleton DatabaseManager instance to avoid creating multiple connection pools
"""

from agent.database.db_manager import DatabaseManager

_db_instance = None

def get_db():
    """Get or create singleton DatabaseManager instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
