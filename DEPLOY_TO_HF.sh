#!/bin/bash
# Deploy HF Space Backend with Authentication
# This script prepares and pushes all changes to Hugging Face

set -e  # Exit on error

echo "=========================================="
echo "🚀 Deploying to Hugging Face Space"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "hf_space" ]; then
    echo -e "${RED}❌ Error: hf_space directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo -e "${GREEN}✅ Found hf_space directory${NC}"
echo ""

# Step 1: Clean up redundant files
echo "=========================================="
echo "Step 1: Cleaning up redundant files"
echo "=========================================="

if [ -f "hf_space/backend/agent/database/cached_database_tools.py" ]; then
    echo "Removing cached_database_tools.py..."
    # Check if file is tracked by git
    if git ls-files --error-unmatch hf_space/backend/agent/database/cached_database_tools.py > /dev/null 2>&1; then
        git rm hf_space/backend/agent/database/cached_database_tools.py
    else
        rm hf_space/backend/agent/database/cached_database_tools.py
    fi
    echo -e "${GREEN}✅ Removed cached_database_tools.py${NC}"
else
    echo -e "${YELLOW}⚠️  cached_database_tools.py already removed${NC}"
fi

if [ -f "hf_space/backend/agent/research_agent/research_tools.py" ]; then
    echo "Removing research_tools.py..."
    # Check if file is tracked by git
    if git ls-files --error-unmatch hf_space/backend/agent/research_agent/research_tools.py > /dev/null 2>&1; then
        git rm hf_space/backend/agent/research_agent/research_tools.py
    else
        rm hf_space/backend/agent/research_agent/research_tools.py
    fi
    echo -e "${GREEN}✅ Removed research_tools.py${NC}"
else
    echo -e "${YELLOW}⚠️  research_tools.py already removed${NC}"
fi

echo ""

# Step 2: Stage all changes
echo "=========================================="
echo "Step 2: Staging changes"
echo "=========================================="

git add hf_space/

echo -e "${GREEN}✅ Changes staged${NC}"
echo ""

# Step 3: Show what's being committed
echo "=========================================="
echo "Step 3: Changes to be committed"
echo "=========================================="
echo ""

git status

echo ""
echo "=========================================="
echo "Modified files:"
echo "=========================================="

git diff --cached --name-only

echo ""

# Step 4: Create commit
echo "=========================================="
echo "Step 4: Creating commit"
echo "=========================================="

COMMIT_MESSAGE="feat: Add JWT authentication system and agent tool improvements

🔒 Authentication System:
- Add JWT authentication with bcrypt password hashing
- Add 8 authentication API endpoints
- Add rate limiting (5 login/min, 3 pwd change/hour)
- Add configurable CORS security
- Integrate auth migration into start.sh (runs automatically on deploy)
- Seed 9 default users with hashed passwords on startup

🛠️ Agent Tools:
- Add 10 missing CRUD tools (list/get/delete for RFPs, briefs, presentations)
- Update database_agent with all new tools (13 total)
- Remove 2 redundant presentation wrapper functions from tools.py

🧹 Code Cleanup:
- Delete cached_database_tools.py (over-engineered caching layer)
- Delete research_tools.py (duplicate of search_agent)
- Reduce codebase by ~240 lines

🚀 Deployment:
- Automatic migration on startup (no manual commands needed)
- User seeding on first run
- Compatible with HF Spaces PostgreSQL + Datasets backup
- All dependencies in requirements.txt

Phases 1-3 complete (50% of refactoring project).

See: COMPLETE_COMMANDS.md, QUICK_REFERENCE.md, MANUAL_SETUP_STEPS.md

Co-Authored-By: Claude <noreply@anthropic.com>"

echo ""
echo "Commit message:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$COMMIT_MESSAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Proceed with commit? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏸️  Deployment cancelled${NC}"
    exit 1
fi

git commit -m "$COMMIT_MESSAGE"

echo -e "${GREEN}✅ Commit created${NC}"
echo ""

# Step 5: Push to remote
echo "=========================================="
echo "Step 5: Pushing to remote"
echo "=========================================="

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"
echo ""

read -p "Push to remote? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏸️  Push cancelled (commit created locally)${NC}"
    exit 0
fi

git push

echo -e "${GREEN}✅ Pushed to remote${NC}"
echo ""

# Step 6: Next steps
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🎉 Your HF Space will now:"
echo "   1. Install authentication dependencies (passlib, python-jose, slowapi)"
echo "   2. Run database migration (add password_hash column)"
echo "   3. Seed 9 users with hashed passwords"
echo "   4. Start with full JWT authentication"
echo ""
echo "📝 Required: Set HF Space Secrets"
echo ""
echo "Go to your HF Space Settings → Secrets and add:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "JWT_SECRET_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Generate a secure key with:"
echo "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
echo ""
echo "Example value:"
echo "  aB3dE5fG7hI9jK0lM2nO4pQ6rS8tU1vW3xY5zA7bC9d"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CORS_ORIGINS (optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Set to your HF Space URL:"
echo "  https://your-username-your-space-name.hf.space"
echo ""
echo "Or leave unset to allow all origins (dev only!)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ACCESS_TOKEN_EXPIRE_MINUTES (optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Default: 1440 (24 hours)"
echo "Set to custom value if needed"
echo ""
echo "=========================================="
echo "🔑 Default User Credentials"
echo "=========================================="
echo ""
echo "Username: admin"
echo "Password: admin123!"
echo ""
echo -e "${YELLOW}⚠️  Change these passwords after first login!${NC}"
echo ""
echo "=========================================="
echo "🧪 Testing Your Deployment"
echo "=========================================="
echo ""
echo "Once your HF Space rebuilds, test authentication:"
echo ""
echo "curl -X POST https://your-space-url.hf.space/api/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"admin\", \"password\": \"admin123!\"}'"
echo ""
echo "You should receive a JWT access token!"
echo ""
echo "=========================================="
echo "📚 Documentation"
echo "=========================================="
echo ""
echo "See these files for more info:"
echo "  - QUICK_REFERENCE.md - Quick setup guide"
echo "  - COMPLETE_COMMANDS.md - All commands and phases"
echo "  - MANUAL_SETUP_STEPS.md - Step-by-step guide"
echo "  - hf_space/backend/AUTH_IMPLEMENTATION.md - Auth details"
echo ""
echo "=========================================="
echo "✨ Happy Deploying!"
echo "=========================================="
