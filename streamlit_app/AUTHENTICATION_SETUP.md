# Authentication Setup Guide

This guide will help you set up user authentication for the GRANITE Bid Assistant.

## Prerequisites

- PostgreSQL database configured and running
- Database schema already initialized
- `bcrypt` installed (included in requirements.txt)

## Setup Steps

### 1. Run Database Migration

Add authentication fields to the `rfp_users` table:

```bash
cd streamlit_app
python -c "
from agent.database.db_singleton import get_db
db = get_db()
with open('agent/database/add_auth_to_users.sql', 'r') as f:
    sql = f.read()
with db._get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()
print('✅ Migration complete')
"
```

### 2. Initialize Users

Create the initial user accounts:

```bash
cd streamlit_app
python initialize_users.py
```

This will create 9 users with the following credentials:

| Username | Password | Full Name |
|----------|----------|-----------|
| paul.wallis | paul-wallis-123! | Paul Wallis |
| lionel.laulhe | lionel-laulhe-123! | Lionel Laulhe |
| bethany.bromfield | bethany-bromfield-123! | Bethany Bromfield |
| sowjanya.gummella | sowjanya-gummella-123! | Sowjanya Gummella |
| sharif.kamyab | sharif-kamyab-123! | Sharif Kamyab |
| anna.fakir | anna-fakir-123! | Anna Fakir |
| rana.alnajjar | rana-alnajjar-123! | Rana Al Najjar |
| ghalya.shamo | ghalya-shamo-123! | Ghalya Shamo |
| nadine.khair | nadine-khair-123! | Nadine Khair |

**Note:** All users will be required to change their password on first login.

### 3. Test Authentication

1. Start the Streamlit app:
   ```bash
   streamlit run Agent.py
   ```

2. You should see a login page
3. Try logging in with any of the default credentials
4. You'll be prompted to change your password
5. After changing your password, you'll be logged in

## Features

### Login/Logout
- Users must log in to access the application
- Logout button available in the sidebar
- Passwords are securely hashed using bcrypt

### Password Management
- Users can change their password via the sidebar
- Minimum password length: 8 characters
- Users must change default password on first login

### Multi-User Support
- **Sessions:** Independent per user (each user has their own chat sessions)
- **RFPs/Reports:** Shared across all users (everyone can view all RFPs and reports)

### Pages Protected
All pages require authentication:
- Main chat interface (Agent.py)
- Download Reports page
- Help page

## Architecture

### Session State
- `st.session_state.authenticated` - Whether user is logged in
- `st.session_state.user` - Current user data (username, full_name, user_id, etc.)
- `st.session_state.show_change_password` - Whether to show password change dialog

### Database Tables
- `rfp_users` - User accounts with authentication
  - `user_id` (UUID)
  - `username` (unique)
  - `password_hash` (bcrypt)
  - `full_name`
  - `is_active`
  - `must_change_password`
  - `email`

### Security
- Passwords are hashed using bcrypt with auto-generated salts
- No plaintext passwords stored in database
- Session-based authentication via Streamlit session state

## Adding New Users

To add new users after initial setup:

```python
from auth import hash_password
from agent.database.db_singleton import get_db

db = get_db()

with db._get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO rfp_users (username, password_hash, full_name, must_change_password)
            VALUES (%s, %s, %s, true)
        """, (
            'new.user',
            hash_password('new-user-123!'),
            'New User'
        ))
        conn.commit()
```

## Troubleshooting

### "Invalid username or password"
- Check username format: `firstname.lastname`
- Verify password is correct
- Check if user exists in database

### "User not found"
- Run the initialize_users.py script
- Check database connection
- Verify migration was successful

### Can't change password
- Ensure old password is correct
- New password must be at least 8 characters
- New password and confirmation must match

## Deployment to Streamlit Cloud

When deploying to Streamlit Cloud:

1. Push all changes to your repository
2. Ensure `bcrypt>=4.0.0` is in requirements.txt
3. After deployment, run the migration and user initialization:
   - Use Streamlit Cloud's terminal access, or
   - Create a one-time setup script that runs on first launch

## Security Best Practices

1. **Change default passwords immediately** after first login
2. **Don't share passwords** between users
3. **Use strong passwords** (mix of letters, numbers, symbols)
4. **Keep bcrypt library updated** for latest security patches
5. **Regularly review active users** and deactivate unused accounts

## Future Enhancements

Potential improvements:
- Password reset functionality
- Email-based authentication
- Two-factor authentication
- Session timeout
- User roles and permissions
- Activity logging
