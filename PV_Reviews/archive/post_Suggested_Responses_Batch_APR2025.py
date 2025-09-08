from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random
import os
import logging
from dotenv import load_dotenv
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def expand_all_reviews(iframe_locator):
    """Click More button until all reviews are loaded, with dynamic retries"""
    retries = 0
    max_retries = 15
    initial_reviews_count = 0
    wait_time = 2  # Initial wait time in seconds
    
    while retries < max_retries:
        try:
            # Count current number of reviews
            reviews = iframe_locator.locator('div[data-review-id]')
            current_reviews_count = reviews.count()
            
            if retries == 0:
                initial_reviews_count = current_reviews_count
                logger.info(f"Initial number of reviews: {initial_reviews_count}")
            
            more_button = iframe_locator.locator('button[aria-label="More Reviews"]')
            if more_button.is_visible(timeout=5000):
                more_button.click()
                time.sleep(wait_time)
                
                # Check if new reviews were loaded
                new_reviews_count = reviews.count()
                if new_reviews_count == current_reviews_count:
                    logger.info("No more reviews loaded, stopping expansion")
                    break
                    
                retries += 1
                wait_time = min(wait_time + 1, 5)
                logger.info(f"Loaded more reviews - attempt {retries}/{max_retries}, reviews now: {new_reviews_count}")
            else:
                logger.info("More Reviews button not visible, stopping expansion")
                break
        except Exception as e:
            logger.warning(f"Error loading more reviews: {e}")
            retries += 1
            wait_time = min(wait_time + 1, 5)
            continue
    
    final_reviews_count = iframe_locator.locator('div[data-review-id]').count()
    logger.info(f"Finished loading reviews after {retries} attempts, total reviews: {final_reviews_count}")

def post_replies_to_reviews(responses_data):
    """Post replies to unreplied Google reviews
    Args:
        responses_data: Either DataFrame or path to CSV file
    """
    if isinstance(responses_data, str):
        df = pd.read_csv(responses_data)
    else:
        df = responses_data.copy()
    
    # Rename response_text to Suggested_Response
    df.rename(columns={'response_text': 'Suggested_Response'}, inplace=True)
    
    # Ensure Review ID is present
    if 'Review ID' not in df.columns:
        logger.error("Review ID column missing in CSV, cannot proceed")
        return
    
    logger.info(f"Processing {len(df)} reviews")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # Login
            page.goto('https://accounts.google.com/')
            time.sleep(random.uniform(2, 5))
            
            email = os.getenv('GOOGLE_EMAIL')
            page.locator('input[type="email"]').fill(email)
            page.click('button:has-text("Next")')
            page.wait_for_selector('input[type="password"]', timeout=30000)
            
            password = os.getenv('GOOGLE_PASSWORD')
            page.locator('input[type="password"]').fill(password)
            page.click('button:has-text("Next")')
            
            page.wait_for_url('https://myaccount.google.com/?pli=1', timeout=20000)
            time.sleep(5)
            
            # Navigate to reviews
            page.goto('https://g.co/kgs/HgU3VjS', timeout=20000)
            read_reviews_button = page.locator('button:has-text("Read reviews")')
            read_reviews_button.click()
            
            iframe_locator = page.frame_locator('iframe[src*="/local/business/11382416837896137085/customers/reviews"]')
            
            # Click Unreplied filter
            unreplied_button = iframe_locator.locator('button:has(span:has-text("Unreplied"))')
            unreplied_button.click()
            
            # Expand all reviews
            expand_all_reviews(iframe_locator)
            
            # Scroll to top
            frame = iframe_locator.first
            time.sleep(2)
            
            successful_replies = 0
            failed_replies = 0
            
            for idx, row in df.iterrows():
                try:
                    review_id = str(row['Review ID'])  # Ensure string type
                    suggested_response = row['Suggested_Response']
                    
                    logger.info(f"Processing review {idx + 1}/{len(df)} (ID: {review_id})")

                    # Locate the specific review element
                    review_element = iframe_locator.locator(f'div[data-review-id="{review_id}"]')
                    
                    # Check if review exists
                    if not review_element.is_visible(timeout=5000):
                        logger.warning(f"Review {review_id} not found on page, skipping")
                        failed_replies += 1
                        continue

                    # Get the container div that has both review and reply button
                    review_container = iframe_locator.locator(f'div.J7elmb:has(div[data-review-id="{review_id}"])')

                    # Check if already replied
                    if review_container.locator('div:has-text("Business reply")').is_visible(timeout=2000):
                        logger.info(f"Review {review_id} already has a reply, skipping")
                        continue

                    # Within this container, get the Reply button
                    reply_button = review_container.locator('button:has(span:text-is("Reply"))')

                    # Check if the button is visible and enabled
                    if reply_button.is_visible(timeout=5000) and reply_button.is_enabled(timeout=5000):
                        reply_button.click()
                    else:
                        logger.error("Reply button not found or not enabled")
                        failed_replies += 1
                        continue
                                                                
                    # Fill response
                    textarea = iframe_locator.locator('textarea[aria-label="Your public reply"]')
                    textarea.fill(suggested_response)
                    
                    # Submit
                    submit_button = iframe_locator.locator('button.VfPpkd-LgbsSe.DuMIQc[jsname="hrGhad"]')
                    submit_button.click()
                    
                    # Verify submission
                    time.sleep(random.uniform(3, 5))
                    if review_container.locator('div:has-text("Business reply")').is_visible(timeout=5000):
                        logger.info(f"Successfully replied to review {review_id}")
                        successful_replies += 1
                    else:
                        logger.warning(f"Reply submission for review {review_id} may have failed")
                        failed_replies += 1
                    
                except Exception as e:
                    logger.error(f"Error posting reply to review {review_id}: {e}")
                    failed_replies += 1
                    continue
                    
            logger.info(f"""
            Reply posting completed:
            - Total reviews processed: {len(df)}
            - Successful replies: {successful_replies}
            - Failed replies: {failed_replies}
            """)
            
        except Exception as e:
            logger.error(f"Error in post_replies_to_reviews: {e}")
        finally:
            browser.close()

def process_in_batches(df, batch_size=25, batch_delay_mins=15):
    total_batches = len(df) // batch_size + (1 if len(df) % batch_size > 0 else 0)
    progress_file = 'reply_progress.json'
    
    # Load progress if exists
    completed_ids = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                content = f.read()
                if content:
                    completed_ids = set(json.loads(content))
        except json.JSONDecodeError:
            logger.warning("Progress file corrupt or empty. Starting fresh.")
            with open(progress_file, 'w') as f:
                json.dump(list(completed_ids), f)
    else:
        with open(progress_file, 'w') as f:
            json.dump(list(completed_ids), f)
            
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(df))
        batch_df = df.iloc[start_idx:end_idx].copy()
        
        logger.info(f"Processing batch {batch_num + 1}/{total_batches}")
        
        # Skip already completed reviews
        batch_df['Review ID'] = batch_df['Review ID'].astype(str)  # Ensure string type for comparison
        batch_df = batch_df[~batch_df['Review ID'].isin(completed_ids)]
        
        if len(batch_df) == 0:
            logger.info("No new reviews to process in this batch, skipping")
            continue
        
        # Process batch
        post_replies_to_reviews(batch_df)
        
        # Update completed IDs
        completed_ids.update(batch_df['Review ID'].tolist())
        with open(progress_file, 'w') as f:
            json.dump(list(completed_ids), f)
            
        if batch_num < total_batches - 1:
            delay = random.uniform(batch_delay_mins * 0.8, batch_delay_mins * 1.2) * 60
            logger.info(f"Batch complete. Pausing for {delay/60:.1f} minutes")
            time.sleep(delay)

if __name__ == "__main__":
    responses_file = 'review_responses_latest.csv'
    
    if os.path.exists(responses_file):
        try:
            # Load the full dataframe
            df = pd.read_csv(responses_file)
            logger.info(f"Loaded {len(df)} reviews from CSV file")
            
            # Process in batches with progress tracking
            process_in_batches(df, batch_size=50, batch_delay_mins=5)
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
    else:
        logger.error(f"Responses file not found: {responses_file}")