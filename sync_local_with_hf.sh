#!/bin/bash
# Sync local PostgreSQL with HF Dataset backup
# This makes your local database identical to the HF Space database

set -e

echo "=========================================="
echo "🔄 Sync Local DB with HF Dataset"
echo "=========================================="
echo ""

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "Loading .env..."
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    exit 1
fi

echo "✅ DATABASE_URL found"
echo ""

# Navigate to hf_space
cd hf_space

echo "1️⃣  Dropping existing local database..."
psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "✅ Database cleared"
echo ""

echo "2️⃣  Running schema initialization..."
psql "$DATABASE_URL" -f backend/database/schema.sql

echo "✅ Schema created"
echo ""

echo "3️⃣  Running authentication migration..."
psql "$DATABASE_URL" -f backend/database/migrations/add_password_hash_to_users.sql

echo "✅ Migration applied"
echo ""

echo "4️⃣  Restoring from HF Dataset..."
cd backend
python3 -c "
import sys
sys.path.insert(0, '.')

from database.hf_sync import HFDatabaseSync
import logging

logging.basicConfig(level=logging.INFO)

sync = HFDatabaseSync()

if sync.backup_exists_on_hf():
    print('   📥 Backup found on HF Datasets')
    if sync.full_restore_cycle():
        print('   ✅ Data restored from HF')
    else:
        print('   ❌ Restore failed')
        sys.exit(1)
else:
    print('   ⚠️  No backup on HF, seeding users instead')
    from database.seed_users import seed_users
    seed_users()
"

cd ..

echo ""
echo "=========================================="
echo "✅ Sync Complete!"
echo "=========================================="
echo ""
echo "Your local database is now identical to HF Space"
echo ""
echo "🔑 Test login:"
echo "   Username: admin"
echo "   Password: admin123!"
echo ""
