#!/usr/bin/env python3
"""
Simple test script to verify database functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.utils.database import ReviewDatabase

def test_database():
    """Test basic database functionality"""
    print("🧪 Testing Database Functionality")
    print("=" * 40)
    
    try:
        # Initialize database
        print("1️⃣  Initializing database connection...")
        db = ReviewDatabase()
        print("✅ Database connection successful")
        
        # Test getting unreplied reviews
        print("\n2️⃣  Testing unreplied reviews query...")
        unreplied = db.get_unreplied_reviews(limit=5)
        print(f"✅ Found {len(unreplied)} unreplied reviews")
        
        for i, review in enumerate(unreplied):
            print(f"   {i+1}. {review['reviewer_name']} - {review['rating']}⭐")
            print(f"      Text: {review['review_text'][:60]}..." if review['review_text'] else "      No text")
        
        # Test getting database stats
        print("\n3️⃣  Testing database stats...")
        stats = db.get_run_summary()
        print(f"✅ Database Statistics:")
        print(f"   📊 Total reviews: {stats.get('total_reviews', 0)}")
        print(f"   💬 Unreplied reviews: {stats.get('unreplied_reviews', 0)}")
        print(f"   📝 Recent runs: {len(stats.get('recent_runs', []))}")
        
        # Test saving a sample response
        print("\n4️⃣  Testing response saving...")
        if unreplied:
            sample_review_id = unreplied[0]['review_id']
            success = db.save_response(
                review_id=sample_review_id,
                response_text="Thank you for your wonderful review! We appreciate your feedback.",
                sentiment="positive",
                issues=""
            )
            print(f"✅ Response save test: {'SUCCESS' if success else 'FAILED'}")
        else:
            print("⚠️  No unreplied reviews to test response saving")
        
        # Test getting pending responses
        print("\n5️⃣  Testing pending responses query...")
        pending = db.get_pending_responses(limit=3)
        print(f"✅ Found {len(pending)} pending responses")
        
        for i, response in enumerate(pending):
            print(f"   {i+1}. Response for: {response.get('reviews', {}).get('reviewer_name', 'Unknown')}")
            print(f"      Response: {response['response_text'][:50]}...")
        
        print("\n🎉 All database tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_database()
    sys.exit(0 if success else 1)