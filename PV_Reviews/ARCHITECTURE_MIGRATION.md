# PV Reviews - Architecture Migration Plan

**Target:** Migrate from CSV-based system to Serverless + Free Database Architecture  
**Cost:** $0/month (free tiers only)  
**Timeline:** ~5 hours total implementation

---

## 🎯 TARGET ARCHITECTURE: GitHub Actions + Supabase (100% Free)

### Current Problems:
- CSV files in gitignored folder = no persistence in CI/CD
- GitHub Actions starts fresh each time = no memory  
- Manual CSV editing for human review = error-prone
- Repository structure confusion (PV_Reviews subfolder)

### Target Solution:
```
GitHub Actions (Daily automation) 
    ↓
Supabase PostgreSQL (Data persistence)
    ↓  
Supabase Dashboard (Human review interface - FREE)
    ↓
GitHub Actions (Post approved responses)
```

---

## 📋 MIGRATION TODO LIST

### Phase 1: Database Setup (30 minutes)
- [ ] **Create Supabase account** - free PostgreSQL database
- [ ] **Design database schema** with tables:
  - `reviews` - all review data + metadata
  - `responses` - AI generated responses  
  - `review_status` - workflow tracking (pending_review, approved, posted, etc.)
- [ ] **Set up database tables** with proper relationships and indexes
- [ ] **Configure Row Level Security** for data protection
- [ ] **Test database connection** from local environment

### Phase 2: Update Data Layer (2 hours)
- [ ] **Create database utilities** (`src/utils/database.py`)
  - Connection management
  - CRUD operations for reviews/responses
  - Status update functions
- [ ] **Update review collector** (`src/collectors/review_collector.py`)
  - Replace CSV logic with database writes
  - Implement duplicate checking via database queries  
  - Handle missing data gracefully
- [ ] **Update response generator** (`src/processors/Generate_Responses.py`)
  - Read unreplied reviews from database
  - Store generated responses with status tracking
  - Add sentiment analysis and issue classification to database
- [ ] **Add proper error handling** and structured logging throughout

### Phase 3: Human Review Interface (30 minutes)  
- [ ] **Configure Supabase dashboard** for human review
  - Set up filtered views (pending_review, approved, etc.)
  - Configure bulk actions (approve multiple, reject, etc.)
  - Set up user-friendly column names and formatting
- [ ] **Create review workflow process**
  - Filter reviews by status  
  - Review AI responses
  - Approve/reject/request revision workflow
- [ ] **Test human review process** end-to-end
- [ ] **Create email notifications** with direct links to dashboard

### Phase 4: Update GitHub Actions (1 hour)
- [ ] **Add Supabase credentials** to GitHub repository secrets
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY` 
  - `SUPABASE_SERVICE_KEY` (for admin operations)
- [ ] **Remove CSV/caching logic** from workflow
- [ ] **Update workflow steps** for database operations:
  - Create data directory (if needed for temp files)
  - Install database dependencies (`supabase-py`)
  - Run collection with database writes
  - Remove artifact upload step  
- [ ] **Add posting workflow** - separate job for approved responses only
- [ ] **Update email notifications** with database statistics

### Phase 5: Migration & Testing (1 hour)
- [ ] **Migrate existing CSV data** to Supabase tables
  - Import `reviews_master_database.csv` to reviews table
  - Set appropriate status for existing reviews
  - Verify data integrity after migration
- [ ] **End-to-end testing**
  - Collection: GitHub Actions → Database
  - Review: Human approval via Supabase dashboard  
  - Posting: Only approved responses posted to Google
- [ ] **Validate duplicate prevention** works across runs
- [ ] **Performance testing** - ensure free tier handles expected load
- [ ] **Backup strategy** - export data periodically

---

## 🗄️ DATABASE SCHEMA DESIGN

### `reviews` table:
- `id` (primary key)
- `review_id` (Google's unique ID)
- `reviewer_name`, `rating`, `review_text`
- `collection_timestamp`
- All existing CSV columns
- `status` (unreplied, has_response, posted)

### `responses` table:  
- `id` (primary key)
- `review_id` (foreign key)
- `response_text` (AI generated)
- `sentiment` (AI classified)
- `issues` (AI identified)
- `generated_timestamp`
- `status` (pending_review, approved, needs_revision, rejected)
- `reviewed_by`, `reviewed_on`
- `posted_on`

### `workflow_logs` table:
- `id`, `run_date`, `reviews_collected`, `responses_generated`, `posts_made`
- `errors`, `duration`, `status`

---

## 💰 COST ANALYSIS (FREE TIERS)

### Supabase Free Tier:
- ✅ 500MB database storage (enough for years of reviews)
- ✅ 50MB file storage  
- ✅ 5GB bandwidth/month
- ✅ Built-in dashboard and admin interface
- ✅ Row Level Security
- ✅ Real-time subscriptions
- ✅ Database backups

### GitHub Actions:
- ✅ 2000 minutes/month free (need ~150/month)
- ✅ Unlimited public repositories
- ✅ Built-in secrets management

### Total Monthly Cost: **$0**

---

## 🚀 BENEFITS OF NEW ARCHITECTURE

### Technical Benefits:
- ✅ **Real database** with proper queries, relationships, backups
- ✅ **No CSV/caching hacks** - proper state management
- ✅ **Built-in web interface** for human review (no custom UI needed)
- ✅ **Scalable** - handles growing data automatically  
- ✅ **Professional workflow** - feels like enterprise software
- ✅ **Better error handling** with structured logging
- ✅ **Data integrity** with foreign keys and constraints

### Operational Benefits:
- ✅ **Zero monthly costs** on free tiers
- ✅ **No server management** - fully managed services
- ✅ **Automatic backups** and disaster recovery
- ✅ **Clean repository structure** - no gitignored data files
- ✅ **Proper human review interface** - no more CSV editing
- ✅ **Audit trail** - full history of all changes
- ✅ **Easy reporting** - SQL queries for analytics

---

## 🔄 ROLLBACK PLAN

If migration fails:
1. **Keep current CSV system** as backup during transition
2. **Export Supabase data** back to CSV if needed
3. **Revert GitHub Actions workflow** to CSV version
4. **Document lessons learned** for future attempts

---

## 📞 HANDOVER NOTES FOR NEW THREAD

**Context:** User lost confidence due to 90min YAML troubleshooting. Current system has structural issues with CSV persistence in GitHub Actions.

**Priority:** Better long-term architecture with minimal costs ($0/month requirement)

**Status:** Migration plan approved, ready for implementation

**Next Steps:** Start with Phase 1 (Database Setup) - should take 30 minutes

**Key Files to Review:**
- `PROJECT_TODO.md` - current progress tracker  
- `src/collectors/review_collector.py` - needs database integration
- `src/processors/Generate_Responses.py` - needs database integration
- `.github/workflows/daily-review-collection.yml` - needs database credentials

**Current Issues to Resolve:**
- GitHub Actions workflow fails due to missing data/ directory
- No persistence of master CSV between runs
- Manual CSV editing for human review workflow

**User Expectations:** Professional solution that "feels like enterprise software" but costs nothing to operate.