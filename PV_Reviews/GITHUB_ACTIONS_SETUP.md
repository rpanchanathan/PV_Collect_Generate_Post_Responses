# GitHub Actions Setup for PV Reviews Automation

## Overview
This system runs automated review collection and response generation using GitHub Actions and Supabase database.

## Required GitHub Secrets

Go to your repository Settings > Secrets and variables > Actions, and add these secrets:

### Google Account
- `GOOGLE_EMAIL`: Your Google account email for My Business access
- `GOOGLE_PASSWORD`: Your Google account password

### Anthropic API
- `ANTHROPIC_API_KEY`: Your Claude API key for response generation

### Supabase Database
- `SUPABASE_URL`: Your Supabase project URL (https://xxx.supabase.co)
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key (starts with `eyJ...`)

## Available Workflows

### 1. Daily Review Collection (`daily-reviews.yml`)
- **Schedule**: Runs automatically daily at 6:00 AM IST
- **Purpose**: Collects new reviews and generates AI responses
- **Manual trigger**: Available with custom parameters

**Manual Parameters:**
- `max_reviews`: Maximum reviews to process (default: 50)
- `generate_responses`: Whether to generate AI responses (default: true)

### 2. System Test (`test-system.yml`)
- **Purpose**: Test system components without full collection
- **Manual trigger only**

**Test Options:**
- `database`: Test database connection and operations
- `responses`: Test AI response generation on existing reviews
- `full-system`: Test all components (database mode only)

## Usage

### Testing the System
1. Go to Actions tab in your GitHub repository
2. Click "Test PV Reviews System"
3. Click "Run workflow"
4. Select test type and run

### Daily Automation
- Runs automatically every day at 6:00 AM IST
- No action required once secrets are configured
- Check Actions tab for run results

### Manual Review Collection
1. Go to Actions tab
2. Click "Daily Review Collection and Response Generation"  
3. Click "Run workflow"
4. Set parameters as needed
5. Click "Run workflow"

## Monitoring

### Success Indicators
- ✅ Green checkmarks in Actions tab
- Database statistics printed in logs
- No error messages in workflow output

### Common Issues
- ❌ Missing secrets: Configure all required secrets
- ❌ API limits: Reduce `max_reviews` parameter
- ❌ Database errors: Check Supabase connection

## Database Access
- View your data at: [Supabase Dashboard](https://supabase.com/dashboard)
- Tables: `reviews`, `review_responses`, `processing_logs`

## Cost Considerations
- **GitHub Actions**: 2,000 free minutes/month
- **Supabase**: Free tier includes 500MB database
- **Anthropic**: Pay per API usage (~$0.003 per review response)

Daily run estimated usage:
- ~5 minutes GitHub Actions time
- ~50 API calls to Anthropic (~$0.15/day)
- Minimal database storage

## Security Notes
- All credentials stored as GitHub encrypted secrets
- Database access restricted to service role
- No sensitive data in workflow logs
- Automatic log cleanup after 7 days