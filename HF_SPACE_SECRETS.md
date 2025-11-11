# Hugging Face Space Secrets Configuration

## 🔐 Required Secrets for Deployment

After deploying to Hugging Face, you **MUST** configure these secrets in your Space settings.

Go to: **Your Space → Settings → Repository secrets**

---

## 1. JWT_SECRET_KEY ⚠️ **REQUIRED**

**Purpose**: Secret key for signing JWT authentication tokens

**How to generate**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example value**:
```
aB3dE5fG7hI9jK0lM2nO4pQ6rS8tU1vW3xY5zA7bC9d
```

**Security**:
- ⚠️ **NEVER commit this to git**
- Generate a unique key for production
- Keep it secret and secure
- If compromised, all JWT tokens can be forged

**In HF Space Settings**:
```
Name: JWT_SECRET_KEY
Value: <paste your generated key>
```

---

## 2. CORS_ORIGINS (Optional but Recommended)

**Purpose**: Control which domains can access your API

**Default**: `*` (allows all origins - OK for development)

**Production value**:
```
https://your-username-your-space-name.hf.space
```

**Multiple origins** (comma-separated):
```
https://your-space.hf.space,https://your-custom-domain.com
```

**Security**:
- Set to your HF Space URL in production
- Prevents other websites from calling your API
- Protects against CSRF attacks

**In HF Space Settings**:
```
Name: CORS_ORIGINS
Value: https://your-username-your-space-name.hf.space
```

---

## 3. ACCESS_TOKEN_EXPIRE_MINUTES (Optional)

**Purpose**: How long JWT tokens remain valid

**Default**: `1440` (24 hours)

**Recommended values**:
- Development: `1440` (24 hours)
- Production: `480` (8 hours) or `720` (12 hours)
- High security: `60` (1 hour)

**In HF Space Settings**:
```
Name: ACCESS_TOKEN_EXPIRE_MINUTES
Value: 1440
```

---

## 4. DATABASE_URL (Should Already Exist)

**Purpose**: PostgreSQL connection string for HF Space database

**Format**:
```
postgresql://user:password@host:port/dbname
```

**Note**: This should already be configured if your Space uses PostgreSQL. The `start.sh` script sets this automatically for the local PostgreSQL instance in the container.

**In HF Space Settings** (if using external PostgreSQL):
```
Name: DATABASE_URL
Value: postgresql://user:pass@host:5432/granite_rfp
```

---

## 5. HF_TOKEN (Should Already Exist)

**Purpose**: Hugging Face API token for dataset backup/restore

**Note**: This is automatically available in HF Spaces for accessing your own datasets.

**Manual setup** (if needed):
1. Go to https://huggingface.co/settings/tokens
2. Create a token with `write` access
3. Add to Space secrets

**In HF Space Settings**:
```
Name: HF_TOKEN
Value: hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📋 Quick Setup Checklist

After deploying, verify these secrets are set:

- [ ] `JWT_SECRET_KEY` - Generated a secure random key
- [ ] `CORS_ORIGINS` - Set to your HF Space URL (optional)
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` - Set to desired duration (optional)
- [ ] `DATABASE_URL` - PostgreSQL connection (should exist)
- [ ] `HF_TOKEN` - HF API token (should exist)

---

## 🧪 Testing After Deployment

### 1. Wait for Space to Rebuild
After setting secrets, your Space will automatically rebuild. This takes 2-5 minutes.

### 2. Check Build Logs
Look for these messages in the build logs:
```
3️⃣.5 Running authentication migration...
   ✅ Authentication migration completed

3️⃣.6 Seeding users with hashed passwords...
   ✅ Users seeded with hashed passwords
```

### 3. Test Login Endpoint
Replace `your-space-url.hf.space` with your actual Space URL:

```bash
curl -X POST https://your-space-url.hf.space/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123!"}'
```

**Expected response**:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "...",
    "username": "admin",
    "email": "admin@granite-mena.com",
    "name": "Admin User"
  },
  "session_id": "..."
}
```

### 4. Test Protected Endpoint
```bash
# Save the token from above
TOKEN="your_access_token_here"

curl https://your-space-url.hf.space/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response**:
```json
{
  "success": true,
  "user": {
    "user_id": "...",
    "username": "admin",
    ...
  }
}
```

---

## 🚨 Troubleshooting

### "Could not validate credentials"
**Cause**: JWT_SECRET_KEY not set or incorrect

**Fix**:
1. Go to Space Settings → Secrets
2. Verify `JWT_SECRET_KEY` exists
3. Restart your Space (Settings → Factory reboot)

### "Rate limit exceeded"
**Cause**: Too many login attempts

**Fix**: Wait 1 minute before trying again (max 5 attempts per minute)

### "Invalid username or password"
**Cause**: Users not seeded or wrong credentials

**Fix**:
1. Check build logs for "Users seeded" message
2. Verify username is `admin` (lowercase)
3. Verify password is `admin123!` (with exclamation)

### CORS errors in browser
**Cause**: CORS_ORIGINS doesn't include your frontend URL

**Fix**:
1. Add your Space URL to CORS_ORIGINS
2. Format: `https://your-username-your-space-name.hf.space`
3. Restart Space

---

## 🔒 Security Best Practices

### After First Deployment:

1. **Change default passwords**:
   ```bash
   curl -X POST https://your-space.hf.space/api/auth/change-password \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"old_password": "admin123!", "new_password": "NewSecurePass123!"}'
   ```

2. **Generate unique JWT_SECRET_KEY**:
   - Don't use example values from documentation
   - Generate fresh for production
   - Never share or commit to git

3. **Set restrictive CORS_ORIGINS**:
   - Don't use `*` in production
   - Only whitelist your Space URL
   - Add custom domains if needed

4. **Monitor rate limits**:
   - Check logs for excessive login attempts
   - Adjust rate limits if needed in `auth/router.py`

5. **Enable HTTPS only**:
   - HF Spaces automatically use HTTPS
   - Never expose authentication over HTTP

---

## 📚 Related Documentation

- **[DEPLOY_TO_HF.sh](DEPLOY_TO_HF.sh)** - Automated deployment script
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick setup guide
- **[AUTH_IMPLEMENTATION.md](hf_space/backend/AUTH_IMPLEMENTATION.md)** - Auth system details
- **[COMPLETE_COMMANDS.md](COMPLETE_COMMANDS.md)** - All commands and phases

---

## 🎯 Default User Credentials

After deployment, these users are automatically created:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123! | Admin |
| shahzeb.naeem | shahzeb123! | User |
| bill.butt | bill123! | User |
| tomy.amasha | tomy123! | User |
| liz.lennon | liz123! | User |
| hassan.ali | hassan123! | User |
| noor.nayyara | noor123! | User |
| shehroze | shehroze123! | User |
| sharif | sharif123! | User |

⚠️ **IMPORTANT**: Change all default passwords after first login!

---

## ✅ Summary

**Minimum required**:
1. Set `JWT_SECRET_KEY` secret
2. Deploy to HF Space
3. Wait for rebuild
4. Test login endpoint
5. Change default passwords

**Recommended**:
1. Set `CORS_ORIGINS` to your Space URL
2. Set `ACCESS_TOKEN_EXPIRE_MINUTES` (optional)
3. Monitor build logs for errors
4. Test all authentication endpoints

---

**Last Updated**: 2025-01-07
**Status**: Ready for deployment ✅
