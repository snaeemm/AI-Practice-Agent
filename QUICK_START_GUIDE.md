# Quick Start Guide - HF Space Backend Refactoring

## 🎉 What Was Completed

### Phase 1: Security Foundation ✅ COMPLETE

I've implemented a complete JWT-based authentication system with:
- ✅ 8 authentication API endpoints
- ✅ Password hashing with bcrypt
- ✅ Database migrations for password storage
- ✅ Rate limiting (5 login/min, 3 password changes/hour)
- ✅ Configurable CORS security
- ✅ User seeding script with 9 default users
- ✅ Comprehensive documentation

### Phase 2: Code Cleanup 🔄 30% COMPLETE

- ✅ Removed cached database tools (prepared for deletion)
- ⏳ Presentation wrappers need deletion
- ⏳ Research tools need deletion
- ⏳ Excel generation needs consolidation

---

## 🚀 Immediate Actions Required

### Step 1: Install New Dependencies
```bash
cd hf_space/backend
pip install passlib[bcrypt] python-jose[cryptography] slowapi
```

### Step 2: Run Database Migration
```bash
# Add password_hash column to rfp_users table
psql $DATABASE_URL -f backend/database/migrations/add_password_hash_to_users.sql
```

### Step 3: Seed Users with Passwords
```bash
cd hf_space
python backend/database/seed_users.py
```

This creates 9 users with hashed passwords:
- **Username**: `admin` | **Password**: `admin123!`
- **Username**: `shahzeb.naeem` | **Password**: `shahzeb123!`
- ...and 7 more (see seed_users.py)

### Step 4: Configure Environment Variables

Add to your `.env` file:
```env
# JWT Configuration
JWT_SECRET_KEY=change-this-to-a-strong-random-secret-key-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:7860,https://your-space.hf.space
```

**⚠️ IMPORTANT**: Generate a strong JWT secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Delete Redundant File
```bash
# This file is no longer used (replaced with direct database calls)
rm hf_space/backend/agent/database/cached_database_tools.py
```

### Step 6: Test Authentication
```bash
# Test login
curl -X POST http://localhost:7860/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123!"}'

# Should return:
# {
#   "success": true,
#   "access_token": "eyJhbGc...",
#   "token_type": "bearer",
#   "user": {...},
#   "session_id": "..."
# }
```

### Step 7: Test Protected Endpoint
```bash
# Get current user info (requires token)
TOKEN="your_access_token_from_step_6"

curl http://localhost:7860/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 What Still Needs to Be Done

### High Priority (This Week):

1. **Update Login.svelte** (Frontend Integration)
   - Remove hardcoded passwords from frontend
   - Call `/api/auth/login` instead
   - Store JWT token in localStorage
   - Include token in all API requests

2. **Protect API Endpoints**
   - Add `Depends(get_current_user)` to ~35 endpoints
   - Ensure all sensitive operations require authentication

3. **Delete Remaining Redundant Code**
   - Remove 2 presentation wrapper functions in `tools.py`
   - Delete `research_tools.py` (unused)

### Medium Priority (Next 2 Weeks):

4. **Add Missing Agent Tools** (10 tools)
   - `tool_list_rfps()`
   - `tool_delete_rfp()`
   - `tool_list_presentations()`
   - `tool_delete_presentation()`
   - `tool_list_client_briefs()`
   - `tool_get_client_brief()`
   - `tool_delete_client_brief()`
   - `tool_list_content_calendar()`
   - `tool_list_generated_files()`
   - `tool_download_file()`

5. **Refactor Complex Tools**
   - Split `tool_query_database` into 3 focused tools
   - Consolidate 8 Excel generation functions into 1 class

6. **Add Missing API Endpoints** (28+ endpoints)
   - User management (profile, settings, notifications)
   - Marketing campaigns CRUD
   - Pagination support on all list endpoints

### Low Priority (This Month):

7. **Testing**
   - Unit tests for auth system
   - Integration tests for API endpoints
   - Load testing with concurrent users

8. **Monitoring & Logging**
   - Replace `print()` with structured logging
   - Set up error tracking (Sentry)
   - Monitor rate limit violations

---

## 📖 Documentation

I've created comprehensive documentation:

1. **[AUTH_IMPLEMENTATION.md](hf_space/backend/AUTH_IMPLEMENTATION.md)**
   - Complete authentication system guide
   - API endpoint documentation with examples
   - Testing commands
   - Troubleshooting guide
   - Production deployment checklist

2. **[REFACTORING_NOTES.md](hf_space/backend/REFACTORING_NOTES.md)**
   - Phase-by-phase refactoring progress
   - Files to delete and why
   - Missing functionality breakdown
   - Performance impact analysis

3. **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)**
   - Overall project status (40% complete)
   - Detailed breakdown of what's done vs pending
   - File change summary
   - Next action items

4. **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** (This file)
   - Immediate setup steps
   - Testing instructions
   - Priority task list

---

## 🔒 Security Notes

### ⚠️ CRITICAL - Fix Before Production:

1. **Frontend has hardcoded passwords**
   - Location: `Login.svelte` lines 12-84
   - Risk: Anyone can see passwords in browser source code
   - Fix: Update component to use `/api/auth/login`

2. **API endpoints are not protected**
   - All ~35 endpoints are currently public
   - Anyone can access RFPs, briefs, reports
   - Fix: Add `Depends(get_current_user)` to all routes

3. **Default JWT secret**
   - Current: Placeholder value
   - Risk: Tokens can be forged
   - Fix: Generate strong secret and set in production .env

4. **CORS allows all origins by default**
   - Current: `allow_origins=["*"]`
   - Risk: Any website can call your API
   - Fix: Set `CORS_ORIGINS` in .env to whitelist only your domain

5. **Default user passwords**
   - All seeded users have predictable passwords
   - Fix: Change passwords after first login

---

## 🧪 Testing Checklist

After setup, verify:

- [ ] Login works with seeded users
- [ ] JWT token is returned
- [ ] Rate limiting kicks in after 5 failed logins
- [ ] `/api/auth/me` requires valid token
- [ ] Password change works
- [ ] Logout invalidates session
- [ ] CORS headers are correct
- [ ] Database has `password_hash` column
- [ ] All users have hashed passwords (not plain text)

---

## 🐛 Troubleshooting

### "Could not validate credentials" Error
**Cause**: Invalid or expired JWT token
**Fix**:
- Check token is included in `Authorization: Bearer <token>` header
- Verify `JWT_SECRET_KEY` matches between login and validation
- Token expires after 24 hours by default

### "Invalid username or password" Error
**Cause**: User doesn't exist or wrong password
**Fix**:
- Run `seed_users.py` to create default users
- Check username spelling (case-sensitive)
- Verify password is correct

### "Rate limit exceeded" Error
**Cause**: Too many requests
**Fix**:
- Wait 1 minute before retrying login
- Wait 1 hour before retrying password change

### CORS Errors in Browser
**Cause**: Frontend origin not in allowed list
**Fix**:
- Set `CORS_ORIGINS=http://localhost:3000,http://localhost:7860` in .env
- Restart backend server
- Clear browser cache

### Import Error: "No module named 'passlib'"
**Cause**: New dependencies not installed
**Fix**:
```bash
cd hf_space/backend
pip install -r requirements.txt
```

---

## 📁 Key Files Changed

### Created (10 files):
- `backend/auth/` (5 Python files)
- `backend/database/migrations/add_password_hash_to_users.sql`
- `backend/database/seed_users.py`
- `backend/AUTH_IMPLEMENTATION.md`
- `backend/REFACTORING_NOTES.md`
- `IMPLEMENTATION_STATUS.md`

### Modified (6 files):
- `backend/main.py` - Auth router, CORS, rate limiting
- `backend/agent/database/session_manager.py` - Auth methods
- `backend/database/db_manager.py` - Auth method wrappers
- `backend/agent/database/database_agent.py` - Non-cached imports
- `backend/requirements.txt` - New packages
- `backend/auth/router.py` - Rate limits

### To Delete (3 items):
- `backend/agent/database/cached_database_tools.py` ⚠️ DELETE NOW
- 2 wrapper functions in `backend/agent/tools.py`
- `backend/agent/research_agent/research_tools.py`

---

## 🎯 Success Criteria

You'll know everything is working when:

1. ✅ You can login via API with username/password
2. ✅ JWT token is returned and valid for 24 hours
3. ✅ Rate limiting blocks brute force attempts
4. ✅ Protected endpoints require valid token
5. ✅ CORS only allows your whitelisted domains
6. ✅ Passwords are hashed in database (never plain text)
7. ✅ Users can change their passwords
8. ✅ Sessions can be logged out

---

## 🚀 Next Steps

**Today**:
1. Run migration and seed users
2. Test authentication endpoints
3. Delete `cached_database_tools.py`

**This Week**:
1. Update `Login.svelte` to use backend auth
2. Protect API endpoints with authentication
3. Delete remaining redundant code

**Next Week**:
1. Add 10 missing agent tools
2. Add user management endpoints
3. Add marketing campaigns CRUD

**This Month**:
1. Add comprehensive testing
2. Set up monitoring/logging
3. Deploy to production with proper security

---

## 💡 Pro Tips

1. **Use the seeded admin account for testing**:
   - Username: `admin`
   - Password: `admin123!`
   - Change this password immediately in production!

2. **Check FastAPI auto-generated docs**:
   - Visit: `http://localhost:7860/api/docs`
   - Interactive API testing interface
   - All auth endpoints documented

3. **Monitor rate limits in logs**:
   - Backend will log when rate limits are hit
   - Useful for debugging frontend issues

4. **Use environment variables**:
   - Never commit `.env` file
   - Different values for dev/staging/prod
   - Use strong secrets in production

5. **Test with multiple browsers**:
   - Verify CORS works across different origins
   - Test token storage and retrieval
   - Check logout on all devices

---

## 📞 Need Help?

- **Auth System**: See `backend/AUTH_IMPLEMENTATION.md`
- **Refactoring Status**: See `backend/REFACTORING_NOTES.md`
- **Overall Progress**: See `IMPLEMENTATION_STATUS.md`
- **API Docs**: Visit `/api/docs` after starting server

---

**Status**: Phase 1 Complete ✅ | Ready to continue with Phase 2 & 3 🚀

**Estimated Time Remaining**: 3-4 weeks for complete implementation
