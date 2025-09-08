# Automated Daily Review Collection Setup

This guide explains how to set up automated daily review collection using GitHub Actions (free tier).

## 🎯 Overview

The automation system:
- ✅ **Runs daily** at 6:30 AM IST (1:00 AM UTC) 
- ✅ **CSV database** storage with master file (`reviews_master_database.csv`)
- ✅ **Email notifications** sent to rajesh@genwise.in
- ✅ **Free hosting** on GitHub Actions (2,000 minutes/month)
- ✅ **Duplicate prevention** across all collection runs
- ✅ **Error handling** and backup system

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
- ✅ **Duplicates Skipped** count
- ✅ **Collection Timestamp**
- ✅ **Error Details** (if any)

### Example Email Subject Lines:
- `✅ PV Reviews Collection - 2025-01-08 06:30: 5 new reviews`
- `✅ PV Reviews Collection - 2025-01-08 06:30: No new reviews`
- `❌ PV Reviews Collection - 2025-01-08 06:30: Failed`

## 🗄️ Data Structure

**Master CSV Database** (`data/reviews_master_database.csv`):
- All review data (name, rating, text, Review ID, timestamps)
- Collection metadata (Collection_Timestamp)
- Comprehensive reviewer information
- Individual ratings (Food, Service, Atmosphere)
- Images and metadata

**Daily Backup Files** (`data/reviews_backup_TIMESTAMP.csv`):
- Timestamped copies of each collection run
- Historical record of daily activity
- Recovery backup in case master file corrupts

## 📁 Data Persistence

- **Master Database**: `data/reviews_master_database.csv` (append-only)
- **Daily Backups**: `data/reviews_backup_YYYYMMDD_HHMMSS.csv` 
- **Artifacts**: GitHub Actions uploads data/ folder for 90-day retention
- **Logs**: Collection logs in GitHub Actions (workflow run history)

## ⚙️ Configuration

### Change Schedule
Edit `.github/workflows/daily-review-collection.yml`:
```yaml
schedule:
  - cron: '0 1 * * *'  # 6:30 AM IST (1:00 AM UTC) daily
```

### Change Email Recipients
Update `RECIPIENT_EMAIL` secret in GitHub.

### Modify Collection Settings
Edit `config/settings.py` for business URL, listing ID, and collection parameters.

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

**Test Review Collection Locally:**
```bash
python src/collectors/review_collector.py
```

**Check Master Database:**
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/reviews_master_database.csv')
print(f'Total reviews: {len(df)}')
print(f'Latest collection: {df[\"Collection_Timestamp\"].max()}')
print(df.head())
"
```

**Generate Responses for Reviews:**
```bash
python src/processors/Generate_Responses.py
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

### Storage:
- **CSV files**: ~1-50MB depending on review volume
- **GitHub storage**: 1GB free ✅
- **Artifacts retention**: 90 days (configurable)

## 🔄 Alternative Platforms

If GitHub Actions limits are exceeded:

1. **Railway**: 500 hours/month free
2. **Render**: Free tier with cron jobs  
3. **Google Cloud Run**: Free tier (limited invocations)
4. **Self-hosted**: Raspberry Pi with cron

## 📈 Scaling Options

For higher volume:
- Switch to PostgreSQL database (Supabase/Neon free tiers)
- Use dedicated email service (SendGrid/Mailgun)
- Deploy to VPS (DigitalOcean $5/month)
- Implement SQLite for better query performance

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