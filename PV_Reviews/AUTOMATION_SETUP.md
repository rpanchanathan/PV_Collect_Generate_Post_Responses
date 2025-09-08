# Automated Daily Review Collection Setup

This guide explains how to set up automated daily review collection using GitHub Actions (free tier).

## 🎯 Overview

The automation system:
- ✅ **Runs daily** at 6:00 AM UTC (11:30 AM IST) 
- ✅ **SQLite database** storage for all reviews
- ✅ **Email summaries** sent to rajesh@genwise.in
- ✅ **Free hosting** on GitHub Actions (2,000 minutes/month)
- ✅ **Persistent data** via GitHub Actions cache + artifacts
- ✅ **Error handling** and retry logic

## 🚀 Setup Instructions

### 1. Push to GitHub Repository

```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Add automated review collection system"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/PV_Reviews.git
git branch -M main
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions

Add the following **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GOOGLE_EMAIL` | your.google@email.com | Google account for My Business |
| `GOOGLE_PASSWORD` | your_password | Google account password |
| `ANTHROPIC_API_KEY` | sk-... | Claude API key for response generation |
| `SENDER_EMAIL` | your.email@gmail.com | Email account for sending notifications |
| `SENDER_PASSWORD` | app_password | App password for email account |
| `RECIPIENT_EMAIL` | rajesh@genwise.in | Where to send daily summaries |
| `SMTP_SERVER` | smtp.gmail.com | SMTP server (Gmail default) |
| `SMTP_PORT` | 587 | SMTP port (Gmail default) |

### 3. Set up Email App Password (Gmail)

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification (must be enabled)
3. App Passwords → Generate new app password
4. Use this app password as `SENDER_PASSWORD` secret

### 4. Enable GitHub Actions

1. Go to repository → Actions tab
2. Enable Actions if prompted
3. The workflow will appear as "Daily Review Collection"

### 5. Test the Setup

**Manual Test:**
1. Go to Actions → Daily Review Collection → Run workflow
2. Check the run logs for any errors
3. Verify email is received

**Scheduled Test:**
- Wait for the next scheduled run (6:00 AM UTC daily)
- Check email for daily summary

## 📊 What You'll Receive Daily

### Email Summary Includes:
- ✅ **Run Status** (Success/Failed)
- ✅ **New Reviews Count**
- ✅ **Total Reviews** in database
- ✅ **Unreplied Reviews** count
- ✅ **Run Duration**
- ✅ **7-Day History** table
- ✅ **Error Details** (if any)

### Example Email Subject Lines:
- `✅ PV Reviews: 5 new reviews collected`
- `✅ PV Reviews: No new reviews (all up to date)`
- `❌ PV Reviews: Collection failed - Authentication error`

## 🗄️ Database Schema

SQLite database stores:

**Reviews Table:**
- All review data (name, rating, text, timestamps)
- Response tracking (generated, posted, replied)
- Collection metadata

**Run Logs Table:**
- Daily run statistics
- Performance metrics
- Error tracking

## 📁 Data Persistence

- **Database**: Stored in GitHub Actions cache (persistent across runs)
- **Backups**: Daily database backups in GitHub artifacts (90-day retention)
- **Logs**: Collection logs in artifacts (30-day retention)

## ⚙️ Configuration

### Change Schedule
Edit `.github/workflows/daily-collection.yml`:
```yaml
schedule:
  - cron: '0 6 * * *'  # 6:00 AM UTC daily
```

### Change Email Recipients
Update `RECIPIENT_EMAIL` secret in GitHub.

### Modify Email Content
Edit `src/utils/notifications.py` for custom email templates.

## 🚨 Troubleshooting

### Common Issues:

**1. Authentication Failed**
- Check `GOOGLE_EMAIL` and `GOOGLE_PASSWORD` secrets
- Ensure 2FA is enabled and app password is used

**2. Email Not Sent**
- Verify `SENDER_EMAIL` and `SENDER_PASSWORD` 
- Check Gmail app password is correct
- Confirm `SMTP_SERVER` and `SMTP_PORT`

**3. Workflow Failed**
- Check Actions tab for error logs
- Verify all secrets are set correctly
- Check GitHub Actions minutes usage

**4. Browser/Playwright Issues**
- Usually resolved by workflow restart
- Check if Google changed their UI (may need code updates)

### Debug Commands:

**Test Email Locally:**
```bash
python -c "
import os
os.environ['SENDER_EMAIL'] = 'your@email.com'
os.environ['SENDER_PASSWORD'] = 'app_password'
os.environ['RECIPIENT_EMAIL'] = 'rajesh@genwise.in'

from src.utils.notifications import EmailNotifier
from src.utils.database import ReviewDatabase

notifier = EmailNotifier()
db = ReviewDatabase()
summary = db.get_run_summary()
notifier.send_daily_summary(summary)
"
```

**Test Database:**
```bash
python -c "
from src.utils.database import ReviewDatabase
db = ReviewDatabase()
print(db.get_run_summary())
"
```

## 💰 Cost Analysis (Free Tier)

### GitHub Actions Free Tier:
- **2,000 minutes/month** (66 minutes/day available)
- **Each run**: ~5-10 minutes
- **Monthly usage**: ~150-300 minutes
- **Cost**: FREE ✅

### Email Costs:
- **Gmail SMTP**: FREE ✅
- **Alternative**: Resend (3,000 emails/month free)

### Database:
- **SQLite file**: ~1-10MB
- **GitHub storage**: 1GB free ✅

## 🔄 Alternative Platforms

If GitHub Actions limits are exceeded:

1. **Railway**: 500 hours/month free
2. **Render**: Free tier with cron jobs  
3. **Google Cloud Run**: Free tier (limited invocations)
4. **Self-hosted**: Raspberry Pi with cron

## 📈 Scaling Options

For higher volume:
- Switch to PostgreSQL (Supabase/Neon free tiers)
- Use dedicated email service (SendGrid/Mailgun)
- Deploy to VPS (DigitalOcean $5/month)

---

## 🚀 Quick Start Checklist

- [ ] Push code to GitHub repository
- [ ] Add all 8 repository secrets
- [ ] Set up Gmail app password
- [ ] Enable GitHub Actions
- [ ] Test with manual workflow run
- [ ] Verify daily email received
- [ ] Monitor first few automated runs

**Need help?** Check the Actions logs or email rajesh@genwise.in