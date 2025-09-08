from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def convert_time_to_datetime(time_str):
    """Convert various time formats to datetime"""
    now = datetime.now()
    
    try:
        if 'hours ago' in time_str:
            hours = int(time_str.split()[0])
            return now - timedelta(hours=hours)
        elif 'days ago' in time_str:
            days = int(time_str.split()[0])
            return now - timedelta(days=days)
        elif 'weeks ago' in time_str:
            weeks = int(time_str.split()[0])
            return now - timedelta(weeks=weeks)
        elif 'months ago' in time_str:
            months = int(time_str.split()[0])
            return now - timedelta(days=months*30)
        else:
            return pd.to_datetime(time_str)
    except:
        return now

def process_reviews_in_order(df):
    """Process the DataFrame to add standardized dates and sort"""
    df['StandardizedTime'] = df['Time'].apply(convert_time_to_datetime)
    return df.sort_values('StandardizedTime', ascending=True)


def expand_all_reviews(iframe_locator):
    """Click More button until all reviews are loaded, max 10 retries"""
    retries = 0
    max_retries = 10
    
    while retries < max_retries:
        try:
            more_button = iframe_locator.locator('button[aria-label="More Reviews"]')
            if more_button.is_visible():
                more_button.click()
                time.sleep(2)
                retries += 1
                logger.info(f"Loaded more reviews - attempt {retries}/{max_retries}")
            else:
                break
        except Exception:
            break
    
    logger.info(f"Finished loading reviews after {retries} attempts")

def post_replies_to_reviews(responses_data):
    """Post replies to unreplied Google reviews
    Args:
        responses_data: Either DataFrame or path to Excel file
    """
    if isinstance(responses_data, str):
        df = pd.read_excel(responses_data)
    else:
        df = responses_data.copy()
    
    df = process_reviews_in_order(df)
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
#            frame.evaluate('window.scrollTo(0, 0)')
            time.sleep(2)
            
            successful_replies = 0
            failed_replies = 0
            
            for idx, row in df.iterrows():
                try:
                    review_id = row['Review ID']
                    suggested_response = row['Suggested_Response']
                    current_time = row['StandardizedTime']
                    next_time = df.iloc[idx + 1]['StandardizedTime'] if idx < len(df) - 1 else None
                    
                    logger.info(f"Processing review {idx + 1}/{len(df)} (ID: {review_id})")

                    # First locate the specific review element
                    review_element = iframe_locator.locator(f'div[data-review-id="{review_id}"]')

                    # Get the container div that has both review and reply button
                    review_container = iframe_locator.locator(f'div.J7elmb:has(div[data-review-id="{review_id}"])')

                    # Within this container, get the Reply button
                    reply_button = review_container.locator('button:has(span:text-is("Reply"))')


                    # Print detailed information about the located button
                    #logger.info(f"Reply button count: {reply_button.count()}")
                    #logger.info(f"Reply button is visible: {reply_button.is_visible()}")
                    #logger.info(f"Reply button is enabled: {reply_button.is_enabled()}")
                    #logger.info(f"Located Reply button: {reply_button}")

                    # Check if the button is visible and enabled
                    if reply_button.is_visible() and reply_button.is_enabled():
                        try:
                            reply_button.click()
                        except Exception as e:
                            logger.error(f"Error clicking Reply button: {e}")
                            #... (handle the error)
                    else:
                        logger.error("Reply button not found or not enabled")
                        #... (handle the error)
                                                                
                    # Fill response
                    textarea = iframe_locator.locator('textarea[aria-label="Your public reply"]')
                    textarea.fill(suggested_response)
                    
                    # Submit
                    submit_button = iframe_locator.locator('button.VfPpkd-LgbsSe.DuMIQc[jsname="hrGhad"]')
                    submit_button.click()
                    
                    time.sleep(random.uniform(3, 5))
                    successful_replies += 1
                    #logger.info(f"Successfully replied to review {review_id}")
                    
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
    
    # Load progress if exists - with error handling
    completed_ids = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                content = f.read()
                if content:  # Only try to load if file has content
                    completed_ids = set(json.loads(content))
        except json.JSONDecodeError:
            logger.warning("Progress file corrupt or empty. Starting fresh.")
            # Create new progress file
            with open(progress_file, 'w') as f:
                json.dump(list(completed_ids), f)
    else:
        # Create new progress file
        with open(progress_file, 'w') as f:
            json.dump(list(completed_ids), f)
            
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(df))
        batch_df = df.iloc[start_idx:end_idx].copy()
        
        logger.info(f"Processing batch {batch_num + 1}/{total_batches}")
        
        # Skip already completed reviews
        batch_df = batch_df[~batch_df['Review ID'].isin(completed_ids)]
        
        if len(batch_df) > 0:
            # Process batch
            post_replies_to_reviews(batch_df)  # Now passing DataFrame directly
            
            # Update completed IDs
            completed_ids.update(batch_df['Review ID'].tolist())
            with open(progress_file, 'w') as f:
                json.dump(list(completed_ids), f)
            
            if batch_num < total_batches - 1:
                delay = random.uniform(batch_delay_mins * 0.8, batch_delay_mins * 1.2) * 60
                logger.info(f"Batch complete. Pausing for {delay/60:.1f} minutes")
                time.sleep(delay)


if __name__ == "__main__":
    responses_file = '/Users/rajeshpanchanathan/Documents/Documents - Mac/PythonWork/PV_Reviews/Automate_Lower Ratings Last 4-6 months.xlsx'
    
    if os.path.exists(responses_file):
        try:
            # Load the full dataframe
            df = pd.read_excel(responses_file)
            df = process_reviews_in_order(df)  # Your existing function to sort/standardize
            logger.info(f"Loaded {len(df)} reviews from Excel file")
            
            # Process in batches with progress tracking
            process_in_batches(df, batch_size=50, batch_delay_mins=5)
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
    else:
        logger.error(f"Responses file not found: {responses_file}")