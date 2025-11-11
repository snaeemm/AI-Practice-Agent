#!/bin/bash
# Start local development server with HF Dataset sync
# This ensures local DB is always in sync with HF Space

set -e

echo "=========================================="
echo "🚀 Starting Local Development Server"
echo "=========================================="
echo ""

# Load .env
if [ -f ".env" ]; then
    echo "📋 Loading .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Check required vars
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env"
    exit 1
fi

if [ -z "$HF_TOKEN" ]; then
    echo "❌ HF_TOKEN not set in .env"
    exit 1
fi

echo "✅ Environment loaded"
echo ""

# Navigate to hf_space/backend
cd hf_space/backend

echo "1️⃣  Checking database schema..."
psql "$DATABASE_URL" -c "SELECT 1 FROM rfp_users LIMIT 1;" > /dev/null 2>&1 || {
    echo "   📊 Initializing schema..."
    psql "$DATABASE_URL" -f database/schema.sql
    psql "$DATABASE_URL" -f database/migrations/add_password_hash_to_users.sql
}

echo "✅ Schema ready"
echo ""

echo "2️⃣  Syncing with HF Dataset..."
python3 -c "
import sys
sys.path.insert(0, '.')

from database.hf_sync import HFDatabaseSync
import logging

logging.basicConfig(level=logging.INFO)

sync = HFDatabaseSync()

if sync.backup_exists_on_hf():
    print('   ☁️  Backup found on HF Datasets')
    if sync.full_restore_cycle():
        print('   ✅ Local DB synced with HF')
    else:
        print('   ⚠️  Restore failed, using existing local data')
else:
    print('   ℹ️  No HF backup, seeding users...')
    from database.seed_users import seed_users
    seed_users()
"

echo ""
echo "3️⃣  Starting background sync (60s interval)..."
python3 -c "
import sys
import os
import time
import threading
import logging

sys.path.insert(0, '.')

from database.hf_sync import HFDatabaseSync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_scheduler():
    sync = HFDatabaseSync()
    interval = 60  # Same as HF Space

    logger.info(f'🔄 Background sync started (every {interval}s)')

    while True:
        try:
            time.sleep(interval)
            logger.info('⏰ Running scheduled sync...')
            sync.full_backup_cycle()
        except Exception as e:
            logger.error(f'❌ Sync error: {e}')

# Start in background
thread = threading.Thread(target=backup_scheduler, daemon=True)
thread.start()

logger.info('✅ Background sync running')

# Keep alive
while True:
    time.sleep(60)
" &

SYNC_PID=$!
echo "   ✅ Background sync running (PID: $SYNC_PID)"
echo ""

echo "4️⃣  Starting FastAPI server..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Server: http://localhost:7860"
echo "📊 API Docs: http://localhost:7860/api/docs"
echo "☁️  Sync: Real-time + every 60s → HF Datasets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    echo "   📦 Final sync to HF..."

    python3 -c "
import sys
sys.path.insert(0, '.')
from database.hf_sync import HFDatabaseSync
sync = HFDatabaseSync()
sync.full_backup_cycle()
"

    echo "   👋 Goodbye!"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start server
uvicorn main:app --host 0.0.0.0 --port 7860 --reload --timeout-keep-alive 300 --limit-concurrency 100
