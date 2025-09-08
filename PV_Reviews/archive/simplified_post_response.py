from playwright.sync_api import sync_playwright
import pandas as pd
import logging
import os
from dotenv import load_dotenv
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def find_review(iframe_locator, review_id):
    """Try to find review directly without scrolling first"""
    try:
        # Look for the KuKPRc div inside noyJyc that has our review ID
        review = iframe_locator.locator(f'div.noyJyc div.KuKPRc[data-review-id="{review_id}"]')
        count = review.count()
        logger.info(f"Found {count} elements for review ID {review_id}")
        return review if count > 0 else None
    except Exception as e:
        logger.error(f"Error finding review: {e}")
        return None

def test_find_reviews(test_file: str):
    df = pd.read_excel(test_file)
    logger.info(f"Loaded {len(df)} reviews from Excel file")
    
    with sync_playwright() as p:
        user_data_dir = "./temp_profile"
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            java_script_enabled=True
        )
        
        page = context.pages[0]
        if not page:
            page = context.new_page()
            
        try:
            logger.info("Navigating to reviews page")
            page.goto('https://g.co/kgs/HgU3VjS')
#            page.wait_for_load_state('networkidle')
            
            logger.info("Clicking Read reviews")
            read_reviews_button = page.locator('button:has-text("Read reviews")')
            read_reviews_button.click()
            
            iframe_locator = page.frame_locator('iframe[src*="/local/business/11382416837896137085/customers/reviews"]')
            iframe = iframe_locator.first
            if iframe:
                logger.info("Successfully found reviews iframe")
                
                # Get all review containers
                containers = iframe.locator('div.noyJyc').all()
                logger.info(f"Total review containers found: {len(containers)}")
                
                # Log first few review IDs for comparison
                for i, container in enumerate(containers[:3]):  # First 3 reviews
                    try:
                        review_div = container.locator('div.KuKPRc')
                        review_id = review_div.get_attribute('data-review-id')
                        logger.info(f"Review {i+1} ID: {review_id}")
                    except Exception as e:
                        logger.error(f"Error getting review ID for review {i+1}: {e}")
                
                # Click Unreplied filter
                unreplied_button = iframe_locator.locator('button:has(span:has-text("Unreplied"))')
                unreplied_button.click()
                time.sleep(2)
                
                # Test finding each review from Excel
                for idx, row in df.iterrows():
                    review_id = row['Review ID']
                    logger.info(f"Testing review {idx + 1}/{len(df)} (ID: {review_id})")
                    
                    review = find_review(iframe_locator, review_id)
                    if review:
                        logger.info(f"Successfully found review {review_id}")
                        is_visible = review.is_visible()
                        logger.info(f"Review {review_id} visibility: {is_visible}")
                    else:
                        logger.warning(f"Could not find review {review_id}")
                    
                    time.sleep(1)
            else:
                logger.error("Could not find reviews iframe")
                
        except Exception as e:
            logger.error(f"Error in test script: {e}")
        finally:
            context.close()

if __name__ == "__main__":
    test_file = '/Users/rajeshpanchanathan/Documents/PythonWork/PV_Reviews/reviews_with_responses_test.xlsx'
    if os.path.exists(test_file):
        test_find_reviews(test_file)
    else:
        logger.error(f"Test file not found: {test_file}")