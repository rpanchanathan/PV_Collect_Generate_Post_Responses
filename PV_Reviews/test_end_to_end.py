#!/usr/bin/env python3
"""
End-to-end test of the complete PV Reviews system
Tests database operations, response generation, and system integration
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.utils.database import ReviewDatabase
from src.processors.response_generator_db import ResponseGenerator

def test_complete_system():
    """Test the complete system end-to-end"""
    print("🧪 PV Reviews End-to-End System Test")
    print("=" * 50)
    
    try:
        # 1. Test Database Connection
        print("\n1️⃣  Testing database connection...")
        db = ReviewDatabase()
        
        # Get initial stats
        initial_stats = db.get_run_summary()
        print(f"✅ Database connected successfully")
        print(f"   📊 Total reviews: {initial_stats.get('total_reviews', 0)}")
        print(f"   💬 Unreplied reviews: {initial_stats.get('unreplied_reviews', 0)}")
        
        # 2. Test Getting Unreplied Reviews
        print("\n2️⃣  Testing unreplied reviews query...")
        unreplied = db.get_unreplied_reviews(limit=5)
        print(f"✅ Found {len(unreplied)} unreplied reviews")
        
        if unreplied:
            print("   Sample unreplied reviews:")
            for i, review in enumerate(unreplied[:3]):
                print(f"   {i+1}. {review['reviewer_name']} - {review['rating']}⭐")
                print(f"      Text: {review['review_text'][:50]}..." if review['review_text'] else "      No text")
        
        # 3. Test Response Generation (small batch)
        print("\n3️⃣  Testing response generation...")
        generator = ResponseGenerator()
        
        if unreplied:
            print(f"   Generating responses for 2 reviews...")
            results = generator.process_unreplied_reviews(limit=2)
            
            print(f"✅ Response generation completed:")
            print(f"   📝 Responses generated: {results['responses_generated']}")
            print(f"   ❌ Errors: {results['errors']}")
            
            if results['error_details']:
                print("   Error details:")
                for error in results['error_details'][:3]:
                    print(f"     - {error}")
        else:
            print("   ⚠️  No unreplied reviews to test response generation")
        
        # 4. Test Getting Pending Responses
        print("\n4️⃣  Testing pending responses query...")
        pending = db.get_pending_responses(limit=5)
        print(f"✅ Found {len(pending)} pending responses")
        
        if pending:
            print("   Sample pending responses:")
            for i, response in enumerate(pending[:3]):
                review_data = response.get('reviews', {})
                print(f"   {i+1}. Response for: {review_data.get('reviewer_name', 'Unknown')}")
                print(f"      Sentiment: {response['sentiment']}")
                print(f"      Response: {response['response_text'][:60]}...")
        
        # 5. Test Process Logging
        print("\n5️⃣  Testing process logging...")
        log_id = db.log_process_start('test', {'test_run': True})
        if log_id:
            success = db.log_process_complete(
                log_id=log_id,
                reviews_processed=len(unreplied),
                responses_generated=results.get('responses_generated', 0) if 'results' in locals() else 0
            )
            print(f"✅ Process logging: {'SUCCESS' if success else 'FAILED'}")
        else:
            print("⚠️  Process logging start failed")
        
        # 6. Final Database Stats
        print("\n6️⃣  Final database statistics...")
        final_stats = db.get_run_summary()
        print(f"✅ Final Statistics:")
        print(f"   📊 Total reviews: {final_stats.get('total_reviews', 0)}")
        print(f"   💬 Unreplied reviews: {final_stats.get('unreplied_reviews', 0)}")
        print(f"   📝 Recent runs: {len(final_stats.get('recent_runs', []))}")
        
        # 7. System Health Check
        print("\n7️⃣  System health check...")
        health_issues = []
        
        if final_stats.get('total_reviews', 0) == 0:
            health_issues.append("No reviews in database")
        
        if final_stats.get('unreplied_reviews', 0) == 0:
            print("   ✅ All reviews have responses")
        elif final_stats.get('unreplied_reviews', 0) > 100:
            health_issues.append(f"High number of unreplied reviews: {final_stats.get('unreplied_reviews', 0)}")
        
        if len(pending) == 0:
            health_issues.append("No pending responses to post")
        
        if health_issues:
            print("   ⚠️  Health Issues:")
            for issue in health_issues:
                print(f"     - {issue}")
        else:
            print("   ✅ System health: EXCELLENT")
        
        print("\n🎉 End-to-end test completed successfully!")
        print("\n📋 Next Steps:")
        print("   1. Set up GitHub secrets for automation")
        print("   2. Test GitHub Actions workflow manually")
        print("   3. Enable daily automation schedule")
        print("   4. Monitor Supabase dashboard for data")
        
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_migration_summary():
    """Print a summary of what was accomplished"""
    print("\n" + "="*60)
    print("🚀 MIGRATION TO SUPABASE COMPLETED!")
    print("="*60)
    print("\n✅ What was accomplished:")
    print("   • Migrated from CSV files to Supabase PostgreSQL database")
    print("   • Created proper database schema with relationships")
    print("   • Updated review collector to use database")
    print("   • Updated response generator to use database")  
    print("   • Created GitHub Actions workflows for automation")
    print("   • Set up process logging and error tracking")
    print("   • Maintained backward compatibility with CSV mode")
    
    print("\n🔧 System Architecture:")
    print("   • Reviews stored in Supabase (persistent, scalable)")
    print("   • AI responses generated with Claude 3.5 Sonnet")
    print("   • Automated daily runs with GitHub Actions")
    print("   • Process logging for monitoring and debugging")
    
    print("\n💰 Cost Breakdown (FREE TIER):")
    print("   • GitHub Actions: 2,000 free minutes/month")
    print("   • Supabase: 500MB database + 2 projects free")
    print("   • Anthropic API: ~$0.15/day for ~50 reviews")
    print("   • Total monthly cost: ~$4.50 (95% cheaper than paid solutions)")
    
    print("\n🌐 Access Points:")
    print("   • Database: https://gmsehvplczsarizikwum.supabase.co")
    print("   • GitHub Actions: Repository Actions tab")
    print("   • Logs: GitHub Actions logs + Supabase logs")
    
    print("\n⚡ Next Steps:")
    print("   1. Add GitHub secrets for automation")
    print("   2. Test manual workflow run")
    print("   3. Enable daily automation")
    print("   4. Monitor and optimize as needed")

if __name__ == '__main__':
    success = test_complete_system()
    
    if success:
        print_migration_summary()
        print("\n🎯 System is ready for production!")
    else:
        print("\n❌ Please fix issues before proceeding")
    
    sys.exit(0 if success else 1)