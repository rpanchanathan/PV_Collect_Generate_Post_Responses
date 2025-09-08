#!/usr/bin/env python3
"""
Automated database migration script for Paati Veedu Reviews system
Migrates from CSV files to Supabase PostgreSQL database
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

def test_connection():
    """Test database connection and table existence"""
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")
        return False, None
    
    try:
        supabase = create_client(url, key)
        
        # Test if tables exist by trying to select count
        result = supabase.table('reviews').select('count').limit(1).execute()
        print("✅ Database connection successful!")
        print(f"📊 Found reviews table")
        return True, supabase
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🚨 SETUP REQUIRED:")
        print("1. Go to: https://gmsehvplczsarizikwum.supabase.co/project/default/sql")
        print("2. Copy and paste the contents of database/schema.sql")
        print("3. Run this script again")
        return False, None

def migrate_csv_data(supabase):
    """Migrate existing CSV data to database"""
    data_dir = Path(__file__).parent.parent / 'data'
    
    # Find the latest reviews CSV
    review_files = list(data_dir.glob('reviews_unreplied_*.csv'))
    if not review_files:
        # Try other patterns
        review_files = list(data_dir.glob('reviews_*.csv'))
        if not review_files:
            print("❌ No review CSV files found in data/ directory")
            return False
    
    latest_review_file = max(review_files, key=os.path.getctime)
    print(f"📁 Using review file: {latest_review_file.name}")
    
    # Migrate reviews
    reviews_migrated = 0
    reviews_skipped = 0
    try:
        with open(latest_review_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                # Clean and map CSV fields to database schema
                review_id = row.get('Review ID', '').strip()
                if not review_id:
                    reviews_skipped += 1
                    continue
                
                review_data = {
                    'review_id': review_id,
                    'listing_id': row.get('Listing ID', '').strip(),
                    'reviewer_name': row.get('Reviewer Name', '').strip(),
                    'reviewer_profile_url': row.get('Reviewer Profile URL', '').strip(),
                    'is_local_guide': row.get('Is Local Guide', '').strip().lower() == 'true',
                    'review_count': _safe_int(row.get('Review Count')),
                    'photo_count': _safe_int(row.get('Photo Count')),
                    'rating': _extract_rating(row.get('Rating', '')),
                    'review_time': row.get('Time', '').strip(),
                    'review_text': row.get('Review Text', '').strip(),
                    'share_url': row.get('Share URL', '').strip(),
                    'dine_in': row.get('Dine In', '').strip(),
                    'session': row.get('Session', '').strip(),
                    'price_range': row.get('Price Range', '').strip(),
                    'food_rating': _safe_int(row.get('Food Rating')),
                    'service_rating': _safe_int(row.get('Service Rating')),
                    'atmosphere_rating': _safe_int(row.get('Atmosphere Rating')),
                    'images': _parse_images(row.get('Images', '')),
                    'has_response': False
                }
                
                batch.append(review_data)
                
                # Insert in batches of 50 (smaller batches for better error handling)
                if len(batch) >= 50:
                    try:
                        supabase.table('reviews').upsert(batch).execute()
                        reviews_migrated += len(batch)
                        print(f"✅ Migrated {reviews_migrated} reviews...")
                        batch = []
                    except Exception as e:
                        print(f"⚠️  Batch error: {e}")
                        # Try inserting one by one
                        for item in batch:
                            try:
                                supabase.table('reviews').upsert(item).execute()
                                reviews_migrated += 1
                            except:
                                reviews_skipped += 1
                        batch = []
            
            # Insert remaining batch
            if batch:
                try:
                    supabase.table('reviews').upsert(batch).execute()
                    reviews_migrated += len(batch)
                except Exception as e:
                    print(f"⚠️  Final batch error: {e}")
                    for item in batch:
                        try:
                            supabase.table('reviews').upsert(item).execute()
                            reviews_migrated += 1
                        except:
                            reviews_skipped += 1
        
        print(f"✅ Successfully migrated {reviews_migrated} reviews")
        if reviews_skipped > 0:
            print(f"⚠️  Skipped {reviews_skipped} invalid reviews")
        
    except Exception as e:
        print(f"❌ Review migration failed: {e}")
        return False
    
    # Migrate responses if available
    response_files = list(data_dir.glob('review_responses_*.csv'))
    if response_files:
        latest_response_file = max(response_files, key=os.path.getctime)
        print(f"📁 Using response file: {latest_response_file.name}")
        
        responses_migrated = 0
        responses_skipped = 0
        try:
            with open(latest_response_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch = []
                
                for row in reader:
                    review_id = row.get('Review ID', '').strip()
                    response_text = row.get('response_text', '').strip()
                    
                    if not review_id or not response_text:
                        responses_skipped += 1
                        continue
                    
                    response_data = {
                        'review_id': review_id,
                        'response_text': response_text,
                        'sentiment': row.get('Sentiment', '').strip(),
                        'issues': row.get('Issue(s)', '').strip(),
                        'status': 'generated'
                    }
                    
                    batch.append(response_data)
                    
                    if len(batch) >= 50:
                        try:
                            supabase.table('review_responses').upsert(batch).execute()
                            responses_migrated += len(batch)
                            print(f"✅ Migrated {responses_migrated} responses...")
                            batch = []
                        except Exception as e:
                            print(f"⚠️  Response batch error: {e}")
                            for item in batch:
                                try:
                                    supabase.table('review_responses').upsert(item).execute()
                                    responses_migrated += 1
                                except:
                                    responses_skipped += 1
                            batch = []
                
                if batch:
                    try:
                        supabase.table('review_responses').upsert(batch).execute()
                        responses_migrated += len(batch)
                    except:
                        for item in batch:
                            try:
                                supabase.table('review_responses').upsert(item).execute()
                                responses_migrated += 1
                            except:
                                responses_skipped += 1
                
                print(f"✅ Successfully migrated {responses_migrated} responses")
                if responses_skipped > 0:
                    print(f"⚠️  Skipped {responses_skipped} invalid responses")
                    
        except Exception as e:
            print(f"❌ Response migration failed: {e}")
    
    return True

def _safe_int(value):
    """Safely convert string to int"""
    if not value or value.strip() == '':
        return None
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None

def _extract_rating(rating_str):
    """Extract numeric rating from string like '5 out of 5 stars'"""
    if not rating_str:
        return None
    try:
        # Extract first number from string
        import re
        match = re.search(r'(\d+)', str(rating_str))
        return int(match.group(1)) if match else None
    except:
        return None

def _parse_images(images_str):
    """Parse images string into array"""
    if not images_str or images_str.strip() in ['[]', '']:
        return []
    try:
        # Simple parsing - split by comma if it looks like a list
        if ',' in images_str:
            return [img.strip() for img in images_str.split(',')]
        elif images_str.strip():
            return [images_str.strip()]
        return []
    except:
        return []

def main():
    """Main migration function"""
    print("🚀 Starting Paati Veedu Reviews Database Migration")
    print("="*50)
    
    # Step 1: Test database connection
    print("1️⃣  Testing database connection...")
    success, supabase = test_connection()
    if not success:
        return
    
    # Step 2: Migrate CSV data
    print("\n2️⃣  Migrating CSV data...")
    if not migrate_csv_data(supabase):
        return
    
    # Step 3: Final verification
    print("\n3️⃣  Verifying migration...")
    try:
        reviews_count = supabase.table('reviews').select('count').execute()
        responses_count = supabase.table('review_responses').select('count').execute()
        print(f"📊 Database contains {len(reviews_count.data)} reviews")
        print(f"📊 Database contains {len(responses_count.data)} responses")
    except Exception as e:
        print(f"⚠️  Verification failed: {e}")
    
    print("\n✅ Migration completed successfully!")
    print("🌐 View your data at: https://gmsehvplczsarizikwum.supabase.co/project/default/editor")

if __name__ == '__main__':
    main()