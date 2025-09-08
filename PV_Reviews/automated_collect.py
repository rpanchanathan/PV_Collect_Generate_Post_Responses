#!/usr/bin/env python3
"""Automated review collection with database storage and email notifications."""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import logging

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from collectors.review_collector import ReviewCollector
from utils.database import ReviewDatabase
from utils.notifications import EmailNotifier
from config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automated_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main automated collection function."""
    start_time = time.time()
    run_date = datetime.now().strftime('%Y-%m-%d')
    
    # Initialize components
    config = Config()
    db = ReviewDatabase()
    notifier = EmailNotifier()
    collector = ReviewCollector(config)
    
    logger.info(f"Starting automated review collection for {run_date}")
    
    try:
        # Collect reviews
        reviews_collected, csv_filename = collector.collect_unreplied_reviews()
        
        if reviews_collected == 0:
            logger.info("No reviews collected - may indicate no unreplied reviews or an error occurred")
            # Still try to get any collected data
            reviews_data = []
        else:
            # Load the collected reviews from CSV if available
            if csv_filename and Path(csv_filename).exists():
                import pandas as pd
                df = pd.read_csv(csv_filename)
                reviews_data = df.to_dict('records')
                logger.info(f"Loaded {len(reviews_data)} reviews from CSV file")
            else:
                reviews_data = []
        
        # Save to database
        total_saved, new_reviews = db.save_reviews(reviews_data)
        logger.info(f"Saved {total_saved} reviews to database ({new_reviews} new)")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the run
        status = "SUCCESS" if reviews_collected >= 0 else "FAILED"
        db.log_run(run_date, reviews_collected, new_reviews, duration, status)
        
        # Get summary and send notification
        summary = db.get_run_summary(days=7)
        success = notifier.send_daily_summary(summary)
        
        if success:
            logger.info("Daily summary email sent successfully")
        else:
            logger.warning("Failed to send daily summary email")
        
        logger.info(f"Automated collection completed in {duration:.2f}s")
        
        # Print summary for logs
        print(f"\n=== DAILY COLLECTION SUMMARY ===")
        print(f"Date: {run_date}")
        print(f"Status: {status}")
        print(f"Reviews Collected: {reviews_collected}")
        print(f"New Reviews: {new_reviews}")
        print(f"Total Reviews in DB: {summary['total_reviews']}")
        print(f"Unreplied Reviews: {summary['unreplied_reviews']}")
        print(f"Duration: {duration:.2f}s")
        print(f"Email Sent: {'Yes' if success else 'No'}")
        print("=" * 33)
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Automated collection failed: {error_msg}")
        
        # Log the failed run
        db.log_run(run_date, 0, 0, duration, "ERROR", error_msg)
        
        # Try to send error notification
        try:
            summary = db.get_run_summary(days=7)
            notifier.send_daily_summary(summary)
        except Exception as email_error:
            logger.error(f"Failed to send error notification: {email_error}")
        
        raise

if __name__ == "__main__":
    main()