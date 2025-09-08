"""Improved Google Reviews collector with better structure and error handling."""
from playwright.sync_api import sync_playwright, Page, FrameLocator
import pandas as pd
import time
import random
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import config
from src.utils.logging_config import setup_logging
from src.utils.database import ReviewDatabase
import glob

logger = setup_logging()

class GoogleAuthenticator:
    """Handles Google account authentication."""
    
    def authenticate(self, page: Page) -> bool:
        """Authenticate with Google account."""
        try:
            logger.info("Starting Google authentication")
            page.goto('https://accounts.google.com/')
            time.sleep(random.uniform(2, 5))
            
            # Fill email
            page.locator('input[type="email"]').fill(config.google_email)
            page.click('button:has-text("Next")')
            page.wait_for_selector('input[type="password"]', timeout=30000)
            
            # Fill password
            page.locator('input[type="password"]').fill(config.google_password)
            page.click('button:has-text("Next")')
            
            # Handle any popup windows that might appear
            time.sleep(3)
            try:
                # Check for common popup/modal close buttons including home/address popups
                close_selectors = [
                    'button[aria-label="Close"]',
                    'button[data-testid="close"]', 
                    'button:has-text("Not now")',
                    'button:has-text("Skip")',
                    'button:has-text("Maybe later")',
                    'button:has-text("No thanks")',
                    'button:has-text("Dismiss")',
                    'button:has-text("Got it")',
                    '[role="dialog"] button',
                    '.modal-close',
                    '[aria-label*="close" i]',
                    '[aria-label*="dismiss" i]',
                    # Home/address related popups
                    'button:has-text("Use precise location")',
                    'button:has-text("Block")',
                    'button:has-text("Allow")',
                    '[data-value="dismiss"]',
                    # QR code popup
                    'button[aria-label="Close QR code"]',
                    'button:has-text("Close QR")',
                    '[aria-label*="QR" i] button'
                ]
                
                for selector in close_selectors:
                    try:
                        close_btn = page.locator(selector).first
                        if close_btn.is_visible(timeout=2000):
                            close_btn.click()
                            logger.info(f"Closed popup using selector: {selector}")
                            time.sleep(1)
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Failed to close popup: {e}")
            
            # Wait for authentication
            page.wait_for_url('https://myaccount.google.com/?pli=1', timeout=60000)
            logger.info("Google authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

class ReviewExtractor:
    """Extracts review data from Google My Business."""
    
    def navigate_to_reviews(self, page: Page) -> Optional[FrameLocator]:
        """Navigate to business reviews and return iframe locator."""
        try:
            logger.info("Navigating to reviews page")
            time.sleep(5)
            page.goto(config.business_url, timeout=20000)
            
            # Handle "Not Now" button if present
            try:
                not_now_button = page.locator('g-raised-button:has-text("Not now")')
                if not_now_button.is_visible():
                    not_now_button.click()
                    logger.info("Dismissed 'Not Now' popup")
            except Exception:
                pass
            
            # Click "Read reviews" button
            read_reviews_button = page.locator('button:has-text("Read reviews")')
            read_reviews_button.click()
            logger.info("Opened reviews panel")
            
            time.sleep(random.uniform(2, 4))
            
            # Locate iframe
            iframe_locator = page.frame_locator(f'iframe[src*="/local/business/{config.business_listing_id}/customers/reviews"]')
            
            # Click "Unreplied" filter
            unreplied_button = iframe_locator.locator('button:has(span:has-text("Unreplied"))')
            unreplied_button.click()
            logger.info("Applied 'Unreplied' filter")
            
            # Load all reviews by handling pagination
            time.sleep(3)  # Wait for initial reviews to load
            self._load_all_reviews(iframe_locator)
            
            return iframe_locator
            
        except Exception as e:
            logger.error(f"Failed to navigate to reviews: {e}")
            return None
    
    def _load_all_reviews(self, iframe_locator) -> None:
        """Load all reviews by handling pagination and scrolling."""
        try:
            logger.info("Loading all reviews with pagination...")
            max_attempts = 30  # Match original working code
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                initial_count = len(iframe_locator.locator('div.noyJyc').all())
                
                # Use the proven working selector from original code
                button_clicked = False
                try:
                    more_reviews_button = iframe_locator.locator('button[aria-label="More Reviews"]')
                    if more_reviews_button.count() > 0 and more_reviews_button.first.is_visible():
                        logger.info(f"Clicking 'More Reviews' button (attempt {attempts})")
                        more_reviews_button.first.click()
                        button_clicked = True
                        time.sleep(3)  # Use original timing
                    else:
                        logger.info("No more 'More Reviews' button found")
                except Exception as e:
                    logger.warning(f"Error clicking 'More Reviews': {e}")
                    # Take screenshot for debugging like original code
                    try:
                        # Access the page from iframe context for screenshot
                        pass  # Screenshot logic can be added if needed
                    except:
                        pass
                
                # If no button found, try scrolling to bottom
                if not button_clicked:
                    try:
                        # Scroll to bottom of reviews container
                        iframe_locator.locator('div[jsrenderer="vYiNxe"]').last.scroll_into_view_if_needed(timeout=3000)
                        time.sleep(random.uniform(1, 3))
                    except:
                        pass
                
                # Check if more reviews loaded
                time.sleep(2)
                new_count = len(iframe_locator.locator('div.noyJyc').all())
                
                if new_count > initial_count:
                    logger.info(f"Loaded more reviews: {initial_count} → {new_count}")
                else:
                    # No new reviews loaded, try one more scroll
                    try:
                        iframe_locator.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(3)
                        final_count = len(iframe_locator.locator('div.noyJyc').all())
                        if final_count <= new_count:
                            logger.info(f"No more reviews to load. Final count: {final_count}")
                            break
                    except:
                        break
            
        except Exception as e:
            logger.warning(f"Error during pagination: {e}")
    
    def extract_review_data(self, review_element, index: int = 0) -> Optional[Dict]:
        """Extract data from a single review element."""
        try:
            # Scroll element into view and wait for it to load
            try:
                review_element.scroll_into_view_if_needed(timeout=10000)
                time.sleep(random.uniform(0.5, 1.5))
            except:
                logger.warning(f"Could not scroll review {index} into view")
            
            # Extract basic review information with increased timeouts
            review_id = review_element.locator('div.KuKPRc').get_attribute('data-review-id', timeout=45000)
            listing_id = review_element.locator('div.KuKPRc').get_attribute('data-listing-id', timeout=45000)
            share_url = review_element.locator('div.KuKPRc').get_attribute('data-share-review-url', timeout=45000)
            
            # Reviewer information
            reviewer_name = review_element.locator('a.PskQHd[jsname="xs1xe"]').inner_text()
            reviewer_profile_url = review_element.locator('a.PskQHd[aria-label*="Link to reviewer profile"]').get_attribute('href')
            
            # Reviewer details parsing
            reviewer_details = self._get_element_text(review_element, 'div.PROnRd.vq72z')
            is_local_guide = "Local Guide" in reviewer_details if reviewer_details else False
            review_count = self._extract_number(reviewer_details, r"(\d+)\s+reviews") if reviewer_details else None
            photo_count = self._extract_number(reviewer_details, r"(\d+)\s+photos") if reviewer_details else None
            
            # Rating and timing
            stars_element = review_element.locator('span[role="img"]')
            review_rating = stars_element.get_attribute('aria-label') if stars_element else "No rating"
            review_time = review_element.locator('span.KEfuhb').inner_text()
            
            # Extract review text
            review_text = self._extract_review_text(review_element)
            
            # Extract additional metadata
            dine_in, session, price_range = self._extract_metadata(review_element)
            
            # Extract individual ratings
            food_rating, service_rating, atmosphere_rating = self._extract_individual_ratings(review_element)
            
            # Extract images
            image_urls = self._extract_images(review_element)
            
            return {
                'Reviewer Name': reviewer_name,
                'Reviewer Profile URL': reviewer_profile_url,
                'Is Local Guide': is_local_guide,
                'Review Count': review_count,
                'Photo Count': photo_count,
                'Rating': review_rating,
                'Time': review_time,
                'Review Text': review_text,
                'Review ID': review_id,
                'Listing ID': listing_id,
                'Share URL': share_url,
                'Dine In': dine_in,
                'Session': session,
                'Price Range': price_range,
                'Food Rating': food_rating,
                'Service Rating': service_rating,
                'Atmosphere Rating': atmosphere_rating,
                'Images': image_urls
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract review data: {e}")
            return None
    
    def _get_element_text(self, locator, selector: str) -> Optional[str]:
        """Safely extract text from element."""
        try:
            return locator.locator(selector).first.inner_text()
        except:
            return None
    
    def _extract_number(self, text: str, pattern: str) -> Optional[int]:
        """Extract number using regex pattern."""
        if not text:
            return None
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None
    
    def _extract_review_text(self, review_element) -> Optional[str]:
        """Extract full review text."""
        try:
            # Try full review button first
            full_review_btn = review_element.locator('a[jsname="ix0Hvc"]').first
            if full_review_btn.is_visible():
                full_review_btn.click()
                return review_element.locator('div[jsname="PBWx0c"]').inner_text()
            else:
                return review_element.locator('div.gyKkFe.JhRJje.Fv38Af').inner_text()
        except:
            return None
    
    def _extract_metadata(self, review_element) -> Tuple[Optional[bool], Optional[str], Optional[str]]:
        """Extract dining metadata."""
        dine_in, session, price_range = None, None, None
        try:
            metadata_spans = review_element.locator('span.PROnRd.mpP9nc').all()
            for span in metadata_spans:
                text = span.inner_text()
                if "Dine in" in text:
                    dine_in = True
                if "Lunch" in text:
                    session = "Lunch"
                elif "Dinner" in text:
                    session = "Dinner"
                if "₹" in text:
                    price_range = text
        except:
            pass
        return dine_in, session, price_range
    
    def _extract_individual_ratings(self, review_element) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract Food, Service, Atmosphere ratings."""
        try:
            ratings_text = review_element.locator('div.fjB0Xb').inner_text()
            food_rating = self._extract_number(ratings_text, r"Food:\s*(\d+)/5")
            service_rating = self._extract_number(ratings_text, r"Service:\s*(\d+)/5")  
            atmosphere_rating = self._extract_number(ratings_text, r"Atmosphere:\s*(\d+)/5")
            return food_rating, service_rating, atmosphere_rating
        except:
            return None, None, None
    
    def _extract_images(self, review_element) -> List[str]:
        """Extract image URLs from review."""
        try:
            images = review_element.locator('img.T3g1hc')
            return [img.get_attribute('src') for img in images.all() if img.get_attribute('src')]
        except:
            return []

class ReviewCollector:
    """Main review collection orchestrator."""
    
    def __init__(self):
        self.authenticator = GoogleAuthenticator()
        self.extractor = ReviewExtractor()
        self.db = ReviewDatabase()
    
    def _get_existing_review_ids(self) -> set:
        """Get all Review IDs from database to prevent duplicates."""
        try:
            # Get all reviews from database and extract IDs
            if config.use_database:
                # Use database
                all_reviews = self.db.client.table('reviews').select('review_id').execute()
                existing_ids = {row['review_id'] for row in all_reviews.data if all_reviews.data}
                logger.info(f"Found {len(existing_ids)} existing review IDs in database")
                return existing_ids
            else:
                # Fall back to CSV (legacy mode)
                existing_ids = set()
                master_db_path = config.data_dir / 'reviews_master_database.csv'
                
                if master_db_path.exists():
                    logger.info(f"Reading master database: {master_db_path}")
                    df = pd.read_csv(master_db_path)
                    
                    if 'Review ID' in df.columns:
                        existing_ids = set(df['Review ID'].dropna().astype(str))
                        logger.info(f"Found {len(existing_ids)} existing review IDs in master database")
                    else:
                        logger.warning("Master database missing 'Review ID' column")
                else:
                    logger.info("Master database not found - will create new one")
                
                return existing_ids
            
        except Exception as e:
            logger.warning(f"Error reading existing reviews: {e}")
            return set()
    
    def collect_unreplied_reviews(self) -> Tuple[int, Optional[str]]:
        """Collect unreplied reviews and save to database."""
        logger.info("Starting review collection process")
        
        # Get existing review IDs to prevent duplicates
        existing_ids = self._get_existing_review_ids()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=config.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent=config.user_agent,
                viewport={'width': config.viewport_width, 'height': config.viewport_height}
            )
            
            page = context.new_page()
            
            try:
                # Authenticate
                if not self.authenticator.authenticate(page):
                    return 0, None
                
                # Navigate to reviews
                iframe_locator = self.extractor.navigate_to_reviews(page)
                if not iframe_locator:
                    return 0, None
                
                # Extract reviews
                reviews_data = []
                duplicates_skipped = 0
                review_elements = iframe_locator.locator('div.noyJyc').all()
                
                logger.info(f"Found {len(review_elements)} review elements")
                
                for i, review_element in enumerate(review_elements):
                    if i >= config.max_reviews:
                        break
                    
                    # Take screenshot every 50 reviews for debugging
                    if i > 0 and i % 50 == 0:
                        try:
                            screenshot_path = config.data_dir / f'debug_screenshot_{i}.png'
                            page.screenshot(path=str(screenshot_path))
                            logger.info(f"Took debug screenshot at review {i}: {screenshot_path}")
                        except Exception as e:
                            logger.warning(f"Failed to take screenshot: {e}")
                        
                    review_data = self.extractor.extract_review_data(review_element, i)
                    if review_data:
                        review_id = str(review_data.get('Review ID', ''))
                        
                        # Check for duplicates
                        if review_id and review_id in existing_ids:
                            duplicates_skipped += 1
                            logger.debug(f"Skipping duplicate review ID: {review_id}")
                            continue
                        
                        reviews_data.append(review_data)
                        logger.info(f"Extracted review {i+1}/{len(review_elements)}: {review_data.get('Reviewer Name', 'Unknown')}")
                    else:
                        logger.warning(f"Failed to extract review {i+1}/{len(review_elements)}")
                
                logger.info(f"Duplicate reviews skipped: {duplicates_skipped}")
                
                # Save to database or CSV based on configuration
                if reviews_data:
                    if config.use_database:
                        # Save to database
                        logger.info(f"Saving {len(reviews_data)} new reviews to database")
                        total_saved, new_reviews = self.db.save_reviews(reviews_data)
                        
                        # Log the collection run
                        timestamp = datetime.now().strftime('%Y-%m-%d')
                        self.db.log_run(
                            run_date=timestamp,
                            reviews_collected=len(reviews_data),
                            new_reviews=total_saved,
                            duration_seconds=0,  # Could be calculated if needed
                            status='completed'
                        )
                        
                        logger.info(f"Successfully saved {total_saved} new reviews to database")
                        return total_saved, "database"
                    else:
                        # Legacy CSV mode
                        df = pd.DataFrame(reviews_data)
                        master_db_path = config.data_dir / 'reviews_master_database.csv'
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        # Add collection timestamp to new reviews
                        df['Collection_Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Append to master database (or create if doesn't exist)
                        if master_db_path.exists():
                            logger.info(f"Appending {len(reviews_data)} new reviews to master database")
                            df.to_csv(master_db_path, mode='a', header=False, index=False, escapechar='\\', doublequote=True, quoting=1)
                        else:
                            logger.info(f"Creating new master database with {len(reviews_data)} reviews")
                            df.to_csv(master_db_path, index=False, escapechar='\\', doublequote=True, quoting=1)
                        
                        # Create timestamped backup copy for this collection run
                        backup_filename = config.data_dir / f'reviews_backup_{timestamp}.csv'
                        df.to_csv(backup_filename, index=False, escapechar='\\', doublequote=True, quoting=1)
                        
                        logger.info(f"Successfully saved {len(reviews_data)} new reviews to master database")
                        logger.info(f"Created backup: {backup_filename}")
                        return len(reviews_data), str(master_db_path)
                
                return 0, None
                
            except Exception as e:
                logger.error(f"Error during review collection: {e}")
                return 0, None
            
            finally:
                browser.close()

def main():
    """Main entry point."""
    collector = ReviewCollector()
    count, filename = collector.collect_unreplied_reviews()
    
    if count > 0:
        print(f"Successfully collected {count} unreplied reviews")
        print(f"Saved to: {filename}")
    else:
        print("No reviews were collected - check logs for errors")

if __name__ == "__main__":
    main()