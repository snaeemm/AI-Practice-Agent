"""
In-memory cache layer for session messages and RFP data.
Provides thread-safe caching with background sync to PostgreSQL.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import queue
import time


@dataclass
class CachedMessage:
    """Represents a cached message"""
    message_id: Optional[str]
    role: str
    content: str
    sequence_number: int
    created_at: datetime


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: Any
    expires_at: datetime


@dataclass
class WriteOperation:
    """Represents a queued write operation"""
    operation_type: str  # 'message', 'session_sync', 'session_update'
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SessionCache:
    """
    In-memory cache for session messages and RFP data.
    Thread-safe with background sync support.
    """

    def __init__(self, default_ttl_seconds: int = 300):  # 5 min default TTL
        self.default_ttl = timedelta(seconds=default_ttl_seconds)

        # Message cache: {session_id: List[CachedMessage]}
        self._message_cache: Dict[str, List[CachedMessage]] = {}

        # RFP data cache: {rfp_id: CacheEntry}
        self._rfp_cache: Dict[str, CacheEntry] = {}

        # Write queue for background sync
        self._write_queue: queue.Queue = queue.Queue()

        # Locks for thread safety
        self._message_lock = threading.Lock()
        self._rfp_lock = threading.Lock()

        # Cache statistics
        self._stats = {
            'message_hits': 0,
            'message_misses': 0,
            'rfp_hits': 0,
            'rfp_misses': 0,
            'queue_size': 0
        }

    # ==================== MESSAGE CACHE ====================

    def get_messages(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached messages for a session.
        Returns None if not cached.
        """
        with self._message_lock:
            if session_id in self._message_cache:
                self._stats['message_hits'] += 1
                messages = self._message_cache[session_id]
                return [
                    {
                        'message_id': msg.message_id,
                        'role': msg.role,
                        'content': msg.content,
                        'sequence_number': msg.sequence_number,
                        'created_at': msg.created_at
                    }
                    for msg in messages
                ]
            else:
                self._stats['message_misses'] += 1
                return None

    def set_messages(self, session_id: str, messages: List[Dict[str, Any]]):
        """Load initial messages into cache from database"""
        with self._message_lock:
            self._message_cache[session_id] = [
                CachedMessage(
                    message_id=msg.get('message_id'),
                    role=msg['role'],
                    content=msg['content'],
                    sequence_number=msg['sequence_number'],
                    created_at=msg['created_at']
                )
                for msg in messages
            ]

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sequence_number: int,
        message_id: Optional[str] = None
    ):
        """
        Append a message to the cache.
        Also queues it for background sync to PostgreSQL.
        """
        with self._message_lock:
            if session_id not in self._message_cache:
                self._message_cache[session_id] = []

            cached_msg = CachedMessage(
                message_id=message_id,
                role=role,
                content=content,
                sequence_number=sequence_number,
                created_at=datetime.utcnow()
            )
            self._message_cache[session_id].append(cached_msg)

        # Queue for background sync
        self.queue_write(WriteOperation(
            operation_type='message',
            session_id=session_id,
            data={
                'role': role,
                'content': content,
                'sequence_number': sequence_number,
                'message_id': message_id
            }
        ))

    def get_next_sequence_number(self, session_id: str) -> int:
        """Get next sequence number from cache without DB query"""
        with self._message_lock:
            if session_id in self._message_cache and self._message_cache[session_id]:
                return max(msg.sequence_number for msg in self._message_cache[session_id]) + 1
            return 1

    def clear_messages(self, session_id: str):
        """Clear cached messages for a session"""
        with self._message_lock:
            if session_id in self._message_cache:
                del self._message_cache[session_id]

    # ==================== RFP DATA CACHE ====================

    def get_rfp_data(self, rfp_id: str, data_type: str) -> Optional[Any]:
        """
        Get cached RFP data by type.
        data_type: 'document', 'raw_data', 'qualification', 'deliverables', 'assignments', 'complete'
        """
        cache_key = f"{rfp_id}:{data_type}"

        with self._rfp_lock:
            if cache_key in self._rfp_cache:
                entry = self._rfp_cache[cache_key]

                # Check if expired
                if datetime.utcnow() < entry.expires_at:
                    self._stats['rfp_hits'] += 1
                    return entry.data
                else:
                    # Expired, remove from cache
                    del self._rfp_cache[cache_key]

            self._stats['rfp_misses'] += 1
            return None

    def set_rfp_data(
        self,
        rfp_id: str,
        data_type: str,
        data: Any,
        ttl_seconds: Optional[int] = None
    ):
        """Cache RFP data with TTL"""
        cache_key = f"{rfp_id}:{data_type}"
        ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else self.default_ttl

        with self._rfp_lock:
            self._rfp_cache[cache_key] = CacheEntry(
                data=data,
                expires_at=datetime.utcnow() + ttl
            )

    def invalidate_rfp(self, rfp_id: str):
        """Invalidate all cached data for an RFP (called after updates)"""
        with self._rfp_lock:
            keys_to_delete = [
                key for key in self._rfp_cache.keys()
                if key.startswith(f"{rfp_id}:")
            ]
            for key in keys_to_delete:
                del self._rfp_cache[key]

    def clear_expired_rfp_cache(self):
        """Remove expired RFP cache entries"""
        with self._rfp_lock:
            now = datetime.utcnow()
            keys_to_delete = [
                key for key, entry in self._rfp_cache.items()
                if now >= entry.expires_at
            ]
            for key in keys_to_delete:
                del self._rfp_cache[key]

    # ==================== WRITE QUEUE ====================

    def queue_write(self, operation: WriteOperation):
        """Add a write operation to the background sync queue"""
        self._write_queue.put(operation)
        self._stats['queue_size'] = self._write_queue.qsize()

    def get_queued_writes(self, max_batch_size: int = 50) -> List[WriteOperation]:
        """Get a batch of queued write operations"""
        operations = []
        try:
            while len(operations) < max_batch_size:
                operation = self._write_queue.get_nowait()
                operations.append(operation)
        except queue.Empty:
            pass

        self._stats['queue_size'] = self._write_queue.qsize()
        return operations

    def queue_session_update(self, session_id: str):
        """Queue session timestamp update"""
        self.queue_write(WriteOperation(
            operation_type='session_update',
            session_id=session_id,
            data={'updated_at': datetime.utcnow()}
        ))

    # ==================== STATISTICS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._message_lock, self._rfp_lock:
            return {
                **self._stats,
                'message_cache_size': len(self._message_cache),
                'rfp_cache_size': len(self._rfp_cache),
                'total_messages_cached': sum(
                    len(msgs) for msgs in self._message_cache.values()
                )
            }

    def reset_stats(self):
        """Reset statistics counters"""
        self._stats = {
            'message_hits': 0,
            'message_misses': 0,
            'rfp_hits': 0,
            'rfp_misses': 0,
            'queue_size': self._write_queue.qsize()
        }
