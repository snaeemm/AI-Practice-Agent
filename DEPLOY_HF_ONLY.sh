#!/bin/bash
# Deploy ONLY HF Space changes (not streamlit_app or other files)

set -e

echo "=========================================="
echo "🚀 Deploying HF Space Changes Only"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check directory
if [ ! -d "hf_space" ]; then
    echo -e "${RED}❌ Error: hf_space directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found hf_space directory${NC}"
echo ""

# Step 1: Reset staging area
echo "=========================================="
echo "Step 1: Resetting staging area"
echo "=========================================="

git reset

echo -e "${GREEN}✅ Staging area cleared${NC}"
echo ""

# Step 2: Remove redundant files
echo "=========================================="
echo "Step 2: Removing redundant files"
echo "=========================================="

if [ -f "hf_space/backend/agent/database/cached_database_tools.py" ]; then
    echo "Removing cached_database_tools.py..."
    rm hf_space/backend/agent/database/cached_database_tools.py
    echo -e "${GREEN}✅ Removed${NC}"
fi

if [ -f "hf_space/backend/agent/research_agent/research_tools.py" ]; then
    echo "Removing research_tools.py..."
    rm hf_space/backend/agent/research_agent/research_tools.py
    echo -e "${GREEN}✅ Removed${NC}"
fi

echo ""

# Step 3: Stage ONLY hf_space changes
echo "=========================================="
echo "Step 3: Staging hf_space changes only"
echo "=========================================="

git add hf_space/

echo -e "${GREEN}✅ hf_space changes staged${NC}"
echo ""

# Step 4: Show what will be committed
echo "=========================================="
echo "Step 4: Changes to be committed"
echo "=========================================="
echo ""

git status --short

echo ""
echo "Files:"
git diff --cached --name-only

echo ""

# Step 5: Confirm
read -p "Proceed with commit? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏸️  Cancelled${NC}"
    exit 1
fi

# Step 6: Commit
echo ""
echo "=========================================="
echo "Step 6: Creating commit"
echo "=========================================="

COMMIT_MESSAGE="feat: Add JWT authentication system to HF Space

🔒 Authentication System:
- Add JWT authentication with bcrypt password hashing
- Add 8 authentication API endpoints (login, logout, change password, etc.)
- Add rate limiting (5 login/min, 3 password changes/hour)
- Add configurable CORS security
- Integrate auth migration into start.sh (runs automatically on deploy)
- Seed 9 default users with hashed passwords on startup

🛠️ Agent Tools Improvements:
- Add 10 missing CRUD tools (list/get/delete for RFPs, briefs, presentations)
- Update database_agent with all new tools (now 13 total tools)
- Remove 2 redundant presentation wrapper functions from tools.py

🧹 Code Cleanup:
- Delete cached_database_tools.py (over-engineered caching layer)
- Delete research_tools.py (duplicate of search_agent)
- Reduce codebase by ~240 lines

🚀 Deployment Features:
- Automatic migration on HF Space startup (no manual commands needed)
- User seeding on first run
- Compatible with HF Spaces PostgreSQL + Datasets backup
- All dependencies in requirements.txt

Technical Details:
- Modified: backend/start.sh (added Steps 3.5 & 3.6 for auth)
- Modified: backend/agent/tools.py (removed wrappers)
- Already has: passlib[bcrypt], python-jose, slowapi in requirements.txt

Phases 1-3 complete (50% of refactoring project).

⚠️  REQUIRED: Set JWT_SECRET_KEY secret in HF Space settings after deploy
See: HF_SPACE_SECRETS.md for instructions

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "$COMMIT_MESSAGE"

echo -e "${GREEN}✅ Commit created${NC}"
echo ""

# Step 7: Push
echo "=========================================="
echo "Step 7: Pushing to remote"
echo "=========================================="

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"
echo ""

read -p "Push to remote? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏸️  Push cancelled${NC}"
    exit 0
fi

git push

echo -e "${GREEN}✅ Pushed to $CURRENT_BRANCH${NC}"
echo ""

# Step 8: Next steps
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🎉 Your HF Space will now rebuild with authentication!"
echo ""
echo "⚠️  CRITICAL: Set HF Space Secret"
echo ""
echo "Go to: Your HF Space → Settings → Repository secrets"
echo ""
echo "Add this secret:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Name:  JWT_SECRET_KEY"
echo "Value: <generate with command below>"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Generate key:"
echo "  python -c \"import secrets; print(secrets.token_urlsafe(32))\""
echo ""
echo "🔑 Default credentials:"
echo "  Username: admin"
echo "  Password: admin123!"
echo ""
echo -e "${YELLOW}⚠️  Change passwords after first login!${NC}"
echo ""
echo "📚 See HF_SPACE_SECRETS.md for full setup guide"
echo ""
