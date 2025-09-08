#!/usr/bin/env python3
"""
Database migration script for Paati Veedu Reviews system
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

def setup_database():
    """Run the initial database schema setup"""
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")
        return False
    
    supabase = create_client(url, key)
    
    # Read and execute schema
    schema_path = Path(__file__).parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    try:
        # Execute the schema (note: supabase-py doesn't have direct SQL execution)
        print("⚠️  Please run the schema manually in Supabase SQL Editor:")
        print(f"📁 Copy contents from: {schema_path}")
        print("🌐 Go to: https://gmsehvplczsarizikwum.supabase.co/project/default/sql")
        print("\n" + "="*50)
        print("SCHEMA SQL TO EXECUTE:")
        print("="*50)
        print(schema_sql[:500] + "..." if len(schema_sql) > 500 else schema_sql)
        print("="*50)
        
        input("\nPress Enter after running the schema in Supabase SQL Editor...")
        
        # Test connection
        result = supabase.table('reviews').select('count').execute()
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def migrate_csv_data():
    """Migrate existing CSV data to database"""
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    supabase = create_client(url, key)
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
    try:
        with open(latest_review_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                # Clean and map CSV fields to database schema
                review_data = {
                    'review_id': row.get('Review ID', '').strip(),
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
                
                # Skip empty review IDs
                if not review_data['review_id']:
                    continue
                    
                batch.append(review_data)
                
                # Insert in batches of 100
                if len(batch) >= 100:
                    supabase.table('reviews').upsert(batch).execute()
                    reviews_migrated += len(batch)
                    print(f"✅ Migrated {reviews_migrated} reviews...")
                    batch = []
            
            # Insert remaining batch
            if batch:
                supabase.table('reviews').upsert(batch).execute()
                reviews_migrated += len(batch)
        
        print(f"✅ Successfully migrated {reviews_migrated} reviews")
        
    except Exception as e:
        print(f"❌ Review migration failed: {e}")
        return False
    
    # Migrate responses if available
    response_files = list(data_dir.glob('review_responses_*.csv'))
    if response_files:
        latest_response_file = max(response_files, key=os.path.getctime)
        print(f"📁 Using response file: {latest_response_file.name}")
        
        responses_migrated = 0
        try:
            with open(latest_response_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch = []
                
                for row in reader:
                    review_id = row.get('Review ID', '').strip()
                    response_text = row.get('response_text', '').strip()
                    
                    if not review_id or not response_text:
                        continue
                    
                    response_data = {
                        'review_id': review_id,
                        'response_text': response_text,
                        'sentiment': row.get('Sentiment', '').strip(),
                        'issues': row.get('Issue(s)', '').strip(),
                        'status': 'generated'
                    }
                    
                    batch.append(response_data)
                    
                    if len(batch) >= 100:
                        supabase.table('review_responses').upsert(batch).execute()
                        responses_migrated += len(batch)
                        print(f"✅ Migrated {responses_migrated} responses...")
                        batch = []
                
                if batch:
                    supabase.table('review_responses').upsert(batch).execute()
                    responses_migrated += len(batch)
                    
                # Update has_response flag for reviews with responses
                supabase.rpc('update_reviews_with_responses').execute()
                
            print(f"✅ Successfully migrated {responses_migrated} responses")
            
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
    
    # Step 1: Setup database schema
    print("1️⃣  Setting up database schema...")
    if not setup_database():
        return
    
    # Step 2: Migrate CSV data
    print("\n2️⃣  Migrating CSV data...")
    if not migrate_csv_data():
        return
    
    print("\n✅ Migration completed successfully!")
    print("🌐 View your data at: https://gmsehvplczsarizikwum.supabase.co/project/default/editor")

if __name__ == '__main__':
    main()