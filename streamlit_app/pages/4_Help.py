import streamlit as st
from auth import require_auth
from styles import apply_custom_styles
from components.sidebar import render_sidebar

st.set_page_config(page_title="Help - Granetic", page_icon="❓")

apply_custom_styles()

if not require_auth():
    st.stop()

render_sidebar("help")

st.title("❓ Help & User Guide")
st.markdown("### Welcome to Granetic - Granite's Process Automation Agent")

st.divider()

st.markdown("""
## 🚀 Getting Started

### First Login
1. Use your username and password provided by your administrator
2. **Username format:** `firstname.lastname` (e.g., `paul.wallis`)
3. **Default password format:** `firstname-lastname-123!` (e.g., `paul-wallis-123!`)
4. You will be required to change your password on first login

### Changing Your Password
1. Click the **🔑 Change Password** button in the sidebar
2. Enter your current password
3. Enter and confirm your new password (minimum 8 characters)
4. Click **Change Password**

### Logging Out
- Click the **🚪 Logout** button in the sidebar anytime

---

## 📝 Working with RFPs

### Sessions
- **Sessions are independent per user** - each user has their own chat sessions
- **RFPs and reports are shared** - all users can see all RFPs and reports
- Create a new session using the **➕ Create New Session** button in the sidebar
- Give your session a descriptive name (e.g., "KHDA RFP Analysis")
- Switch between sessions using the dropdown in the sidebar

### Processing RFPs
1. Upload an RFP document in the chat interface
2. The system will:
   - Extract key information (client, project, deadlines, deliverables)
   - Check for duplicates
   - Qualify the RFP based on fit and feasibility
   - Match against capabilities
   - Generate assignment recommendations
3. Ask questions about the RFP in the chat
4. Request bid plans, reports, and analysis

### Downloading Reports
1. Navigate to the **📥 Download Reports** page
2. View all generated reports for all RFPs
3. Download Excel reports including:
   - Qualification reports
   - Assignment analysis
   - Bid plans
   - Deliverables breakdown

---

## 🔍 Key Features

### RFP Deduplication
- The system automatically detects duplicate RFPs based on client name and project title
- If a duplicate is found, you'll be notified and can choose to continue or cancel

### Multi-User Support
- All users share access to RFPs and reports
- Each user has independent chat sessions
- Your sessions won't appear in other users' lists

### Session Management
- **Close Session:** Temporarily close a session (data is preserved)
- **Delete Session:** Permanently delete a session and all its messages
- View active RFP for each session

---

## 💡 Tips & Best Practices

1. **Session Naming:** Use descriptive names that include the client or project name
2. **Password Security:** Change your default password immediately after first login
3. **Session Organization:** Create separate sessions for different RFPs or projects
4. **Reports Access:** All generated reports are available to all users in the Downloads page

---

## 🐛 Troubleshooting

### "Failed to load session"
- Try refreshing the page
- If the issue persists, create a new session

### "Invalid username or password"
- Check your username format (should be `firstname.lastname`)
- Check for typos in your password
- Contact your administrator if you've forgotten your password

### Can't see expected RFPs
- Remember: RFPs are shared across all users
- Check the Downloads page for all available reports

---

## 📞 Support

For technical issues or questions, contact your system administrator.

---

**Version:** 1.0
**Last Updated:** October 2025
""")

st.divider()

with st.expander("🔧 Advanced Features (Coming Soon)"):
    st.markdown("""
    - **Report Filters:** Filter reports by date, client, status
    - **RFP Dashboard:** Visual overview of all RFPs and their status
    - **Team Collaboration:** Comment and tag other users on RFPs
    - **Email Notifications:** Get notified about new RFPs and updates
    - **Custom Templates:** Create and manage custom bid plan templates
    """)
