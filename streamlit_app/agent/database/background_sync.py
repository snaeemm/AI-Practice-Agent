"""
Background thread for syncing cached writes to PostgreSQL.
Runs as a daemon thread with periodic batch flushing.
"""

import threading
import time
from typing import List
from datetime import datetime
import traceback

from .session_cache import SessionCache, WriteOperation
from .db_manager import DatabaseManager


class BackgroundSyncThread:
    """
    Background daemon thread that periodically flushes queued writes to PostgreSQL.
    """

    def __init__(
        self,
        cache: SessionCache,
        db_manager: DatabaseManager,
        flush_interval_seconds: float = 2.0,
        cleanup_interval_seconds: int = 60
    ):
        self.cache = cache
        self.db = db_manager
        self.flush_interval = flush_interval_seconds
        self.cleanup_interval = cleanup_interval_seconds

        self._thread: threading.Thread = None
        self._stop_event = threading.Event()
        self._last_cleanup = time.time()

    def start(self):
        """Start the background sync thread"""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background sync thread"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self):
        """Main loop for background sync"""
        while not self._stop_event.is_set():
            try:
                # Flush queued writes
                self._flush_writes()

                # Periodic cleanup
                if time.time() - self._last_cleanup > self.cleanup_interval:
                    self._cleanup_expired_cache()
                    self._last_cleanup = time.time()

            except Exception as e:
                print(f"[BackgroundSync] Error in sync loop: {e}")
                traceback.print_exc()

            # Sleep until next flush
            self._stop_event.wait(self.flush_interval)

    def _flush_writes(self):
        """Batch flush queued writes to PostgreSQL"""
        operations = self.cache.get_queued_writes(max_batch_size=50)

        if not operations:
            return  # Nothing to flush

        # Group operations by type for efficient batching
        messages_by_session = {}
        session_updates = set()

        for op in operations:
            if op.operation_type == 'message':
                if op.session_id not in messages_by_session:
                    messages_by_session[op.session_id] = []
                messages_by_session[op.session_id].append(op)

            elif op.operation_type == 'session_update':
                session_updates.add(op.session_id)

            # Note: session_sync operations are handled by Google's ADK automatically

        # Execute batched writes
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. Batch insert messages per session
                    for session_id, msg_ops in messages_by_session.items():
                        self._batch_insert_messages(cursor, session_id, msg_ops)

                    # 2. Batch session timestamp updates
                    if session_updates:
                        self._batch_update_sessions(cursor, list(session_updates))

                    conn.commit()

        except Exception as e:
            print(f"[BackgroundSync] Error flushing writes: {e}")
            traceback.print_exc()
            # On error, re-queue operations
            for op in operations:
                self.cache.queue_write(op)

    def _batch_insert_messages(
        self,
        cursor,
        session_id: str,
        operations: List[WriteOperation]
    ):
        """Batch insert messages for a session"""
        try:
            # Build batch insert values
            values = []
            for op in operations:
                data = op.data
                values.append((
                    session_id,
                    data['role'],
                    data['content'],
                    data['sequence_number'],
                    op.timestamp
                ))

            if not values:
                return

            # Single batch INSERT for all messages
            insert_query = """
                INSERT INTO rfp_messages
                (session_id, role, content, sequence_number, created_at)
                VALUES %s
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, insert_query, values)

            # Single UPDATE for session timestamp
            cursor.execute("""
                UPDATE rfp_sessions
                SET updated_at = %s
                WHERE session_id = %s::uuid
            """, (datetime.utcnow(), session_id))

        except Exception as e:
            print(f"[BackgroundSync] Error inserting messages for session {session_id}: {e}")
            raise

    def _batch_update_sessions(self, cursor, session_ids: List[str]):
        """Batch update session timestamps"""
        try:
            if not session_ids:
                return

            cursor.execute("""
                UPDATE rfp_sessions
                SET updated_at = %s
                WHERE session_id = ANY(%s::uuid[])
            """, (datetime.utcnow(), session_ids))

        except Exception as e:
            print(f"[BackgroundSync] Error updating session timestamps: {e}")
            raise

    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            self.cache.clear_expired_rfp_cache()
        except Exception as e:
            print(f"[BackgroundSync] Error cleaning up cache: {e}")


def create_background_sync(
    cache: SessionCache,
    db_manager: DatabaseManager,
    flush_interval_seconds: float = 2.0
) -> BackgroundSyncThread:
    """
    Factory function to create and start a background sync thread.
    """
    sync_thread = BackgroundSyncThread(
        cache=cache,
        db_manager=db_manager,
        flush_interval_seconds=flush_interval_seconds
    )
    sync_thread.start()
    return sync_thread
