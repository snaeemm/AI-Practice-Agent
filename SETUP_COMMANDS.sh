#!/bin/bash
# HF Space Backend - Complete Setup Commands
# Run this script from the project root directory
# Usage: bash SETUP_COMMANDS.sh

set -e  # Exit on error

echo "=========================================="
echo "HF Space Backend Setup - Phase 1-3"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "hf_space" ]; then
    echo -e "${RED}❌ Error: hf_space directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo -e "${GREEN}✅ Found hf_space directory${NC}"
echo ""

# Step 1: Check environment variables
echo "=========================================="
echo "Step 1: Checking environment variables"
echo "=========================================="

if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL not set${NC}"
    if [ -f ".env" ]; then
        echo "Loading from .env file..."
        export $(grep -v '^#' .env | xargs)
    fi
fi

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL is required${NC}"
    echo "Please set it in your environment or .env file"
    exit 1
fi

echo -e "${GREEN}✅ DATABASE_URL is set${NC}"
echo ""

# Step 2: Install dependencies using UV
echo "=========================================="
echo "Step 2: Installing dependencies with UV"
echo "=========================================="

cd hf_space

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV is not installed${NC}"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "Installing authentication dependencies..."
uv pip install passlib[bcrypt] python-jose[cryptography] slowapi

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 3: Run database migration
echo "=========================================="
echo "Step 3: Running database migration"
echo "=========================================="

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ psql is not installed${NC}"
    echo "Please install PostgreSQL client tools"
    exit 1
fi

echo "Adding password_hash column to rfp_users table..."
psql "$DATABASE_URL" -f backend/database/migrations/add_password_hash_to_users.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration completed${NC}"
else
    echo -e "${YELLOW}⚠️  Migration may have already been applied (safe to ignore)${NC}"
fi
echo ""

# Step 4: Seed users with hashed passwords
echo "=========================================="
echo "Step 4: Seeding users with hashed passwords"
echo "=========================================="

echo "Creating 9 default users..."
uv run python backend/database/seed_users.py

echo -e "${GREEN}✅ Users seeded successfully${NC}"
echo ""

# Step 5: Generate JWT secret key
echo "=========================================="
echo "Step 5: Generating JWT secret key"
echo "=========================================="

JWT_SECRET=$(uv run python -c "import secrets; print(secrets.token_urlsafe(32))")

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Add this to your .env file:${NC}"
echo ""
echo "JWT_SECRET_KEY=$JWT_SECRET"
echo ""
echo "Also add these if not already present:"
echo "ACCESS_TOKEN_EXPIRE_MINUTES=1440"
echo "CORS_ORIGINS=http://localhost:7860,https://your-space.hf.space"
echo ""

# Step 6: Delete redundant files
echo "=========================================="
echo "Step 6: Cleaning up redundant files"
echo "=========================================="

echo "Deleting cached_database_tools.py..."
if [ -f "backend/agent/database/cached_database_tools.py" ]; then
    rm backend/agent/database/cached_database_tools.py
    echo -e "${GREEN}✅ Deleted cached_database_tools.py${NC}"
else
    echo -e "${YELLOW}⚠️  File already deleted or not found${NC}"
fi

echo "Deleting research_tools.py..."
if [ -f "backend/agent/research_agent/research_tools.py" ]; then
    rm backend/agent/research_agent/research_tools.py
    echo -e "${GREEN}✅ Deleted research_tools.py${NC}"
else
    echo -e "${YELLOW}⚠️  File already deleted or not found${NC}"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Summary of changes:"
echo "  ✅ Phase 1: JWT authentication system installed"
echo "  ✅ Phase 2: Database migration applied"
echo "  ✅ Phase 3: 9 users seeded with hashed passwords"
echo "  ✅ Redundant files deleted"
echo ""
echo "📝 Next steps:"
echo "  1. Add JWT_SECRET_KEY to your .env file (shown above)"
echo "  2. Update CORS_ORIGINS for your HF Space URL"
echo "  3. Test authentication endpoints:"
echo ""
echo "     curl -X POST http://localhost:7860/api/auth/login \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"username\": \"admin\", \"password\": \"admin123!\"}'"
echo ""
echo "  4. Check API documentation at: http://localhost:7860/api/docs"
echo ""
echo "🔒 Default credentials:"
echo "   Username: admin"
echo "   Password: admin123!"
echo ""
echo -e "${YELLOW}⚠️  Remember to change default passwords in production!${NC}"
echo ""
echo "📚 See COMPLETE_COMMANDS.md for testing and next phases"
echo ""
