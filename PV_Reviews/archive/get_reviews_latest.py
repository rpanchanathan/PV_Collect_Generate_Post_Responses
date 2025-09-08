from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time
import random
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import re

# Load environment variables
load_dotenv()

# Constants
MAX_REVIEWS = 500  # Increased from 20 to allow for more reviews
OUTPUT_DIR = "/Users/rajeshpanchanathan/Library/CloudStorage/GoogleDrive-rajesh@genwise.in/My Drive/PV/Auto_Review_Response"

# Modified to work with iframe locator
def handle_more_reviews(page, iframe_locator):
    click_count = 0
    max_clicks = 30  # Safety limit to prevent infinite loops
    
    print("Starting to click 'More Reviews' button...")
    
    while click_count < max_clicks:
        try:
            # Look for the "More Reviews" button inside the iframe
            more_reviews_button = iframe_locator.locator('button[aria-label="More Reviews"]')
            
            # Check if button exists and is visible
            if more_reviews_button.count() > 0 and more_reviews_button.first.is_visible():
                print(f"Clicking 'More Reviews' button (click #{click_count+1})")
                more_reviews_button.first.click()
                time.sleep(3)  # Allow time for new reviews to load
                click_count += 1
            else:
                print("No more 'More Reviews' button found. All reviews loaded.")
                break  # Exit the loop if the button is not found
                
        except Exception as e:
            print(f"Error clicking 'More Reviews': {e}")
            # Take a screenshot to debug the issue
            page.screenshot(path=f"more_reviews_error_{click_count}.png")
            time.sleep(2)  # Brief pause before retrying
            
            # If we've had multiple errors, break out
            if click_count > 0:
                break
    
    print(f"Finished clicking 'More Reviews' button {click_count} times")
    return click_count

def collect_reviews():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )

        page = context.new_page()
        
        metadata = {
            'business_id': 'PV',
            'extraction_date': datetime.now().isoformat(),
            'reviews': []
        }
        
        try:
            # Go to Google sign-in
            page.goto('https://accounts.google.com/')
            time.sleep(random.uniform(2, 5))
            
            # Fill email and click next
            email = os.getenv('GOOGLE_EMAIL')
            page.locator('input[type="email"]').fill(email)
            page.click('button:has-text("Next")')
            page.wait_for_selector('input[type="password"]', timeout=30000)
            
            # Fill password and click next
            password = os.getenv('GOOGLE_PASSWORD')
            page.locator('input[type="password"]').fill(password)
            page.click('button:has-text("Next")')
                    
            # Wait for navigation to confirm login
            page.wait_for_url('https://myaccount.google.com/?pli=1', timeout=20000)
            print("Login successful!")
            
            # Short delay before navigating to desired URL
            time.sleep(5)
            page.goto('https://g.co/kgs/HgU3VjS', timeout=20000)
            
            # Handle "Not Now" button
            try:
                not_now_button = page.locator('g-raised-button:has-text("Not now")')
                not_now_button.click()
                print("Clicked 'Not Now' button.")
            except Exception:
                print("Could not find or click 'Not Now' button.")
            
            print("Successfully navigated!")

            # Wait for the "Read reviews" button and click it
            try:
                read_reviews_button = page.locator('button:has-text("Read reviews")')
                read_reviews_button.click()
                print("Clicked 'Read reviews' button.")
            except Exception as e:
                print(f"Could not click 'Read reviews' button: {e}")

            time.sleep(random.uniform(2, 4))

            # Wait for the iframe to appear after clicking "Read reviews"
            try:
                # Locate the iframe based on its `src` attribute or other properties
                iframe_locator = page.frame_locator('iframe[src*="/local/business/11382416837896137085/customers/reviews"]')
                print("Located iframe successfully.")
            except Exception as e:
                print(f"Could not locate iframe: {e}")

            # Interact with the "Unreplied" button inside the iframe
            try:
                # Wait for the "Unreplied" button inside the iframe to appear
                unreplied_button = iframe_locator.locator('button:has(span:has-text("Unreplied"))')
                unreplied_button.click()
                print("Clicked 'Unreplied' button inside iframe.")
                # Wait for content to load after filter is applied
                time.sleep(4)
            except Exception as e:
                print(f"Could not click 'Unreplied' button inside iframe: {e}")
            
            # IMPORTANT: Call handle_more_reviews here, after navigating to reviews and applying filter
            # This is the critical fix - moving the function call to the right place
            click_count = handle_more_reviews(page, iframe_locator)
            print(f"Clicked 'More Reviews' button {click_count} times to load all reviews")
            
            # Allow time for all reviews to fully load after clicking buttons
            time.sleep(5)
            
            # Create an empty list to store review data
            reviews_data = []

            def get_element_text(locator, selector):
                try:
                    return locator.locator(selector).first.inner_text()
                except:
                    alternative_selectors = [
                        f"{selector}:first-child",
                        f"{selector}:not(.Fv38Af)",
                        f"{selector}:has-text('Local Guide')"
                    ]
                    for alt_selector in alternative_selectors:
                        try:
                            return locator.locator(alt_selector).inner_text()
                        except:
                            pass
                return None

            # Locate all review elements on the page
            review_elements = iframe_locator.locator('div.noyJyc').all()
            total_reviews = len(review_elements)
            print(f"Found {total_reviews} reviews to extract")

            # Loop through each review
            for i, review in enumerate(review_elements):
                try:
                    # Print progress
                    if i % 10 == 0:
                        print(f"Processing review {i+1}/{total_reviews}")
                        
                    # Extract unique identifiers
                    review_id = review.locator('div.KuKPRc').get_attribute('data-review-id')
                    listing_id = review.locator('div.KuKPRc').get_attribute('data-listing-id')
                    share_url = review.locator('div.KuKPRc').get_attribute('data-share-review-url')

                    # Extract reviewer name, and other details
                    reviewer_name = review.locator('a.PskQHd[jsname="xs1xe"]').inner_text()
                    reviewer_profile_url = review.locator('a.PskQHd[aria-label*="Link to reviewer profile"]').get_attribute('href')
                    reviewer_details = get_element_text(review, 'div.PROnRd.vq72z')  # e.g., "Local Guide • 36 reviews • 7 photos"
                    
                    # Parse reviewer details
                    is_local_guide = reviewer_details and "Local Guide" in reviewer_details
                    review_count = None
                    photo_count = None
                    
                    if reviewer_details:
                        if "reviews" in reviewer_details:
                            match = re.search(r"(\d+)\s+reviews", reviewer_details)
                            if match:
                                review_count = int(match.group(1))
                        if "photos" in reviewer_details:
                            match = re.search(r"(\d+)\s+photos", reviewer_details)
                            if match:
                                photo_count = int(match.group(1))
                    
                    # Extract review rating (count the number of stars)
                    stars_element = review.locator('span[role="img"]')
                    review_rating = stars_element.get_attribute('aria-label') if stars_element.count() > 0 else "No rating"
                    
                    # Extract review time
                    review_time = review.locator('span.KEfuhb').inner_text()

                    # Review metadata
                    dine_in = None
                    session = None
                    price_range = None
                    metadata_spans = review.locator('span.PROnRd.mpP9nc').all()
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

                    # Extract Full Review and Ratings (Food, Service, Atmosphere)
                    full_review_btn = review.locator('a[jsname="ix0Hvc"]').first
                    review_text = None
                    food_rating = None
                    service_rating = None
                    atmosphere_rating = None
                    
                    if full_review_btn.count() > 0 and full_review_btn.is_visible():
                        full_review_btn.click()
                        time.sleep(0.5)  # Brief pause for content to display
                        review_text = review.locator('div[jsname="PBWx0c"]').inner_text()
                        ratings_section = review.locator('div.fjB0Xb')
                        
                        if ratings_section.count() > 0:
                            ratings_text = ratings_section.inner_text()
                            food_match = re.search(r"Food:\s*(\d+)/5", ratings_text)
                            service_match = re.search(r"Service:\s*(\d+)/5", ratings_text)
                            atmosphere_match = re.search(r"Atmosphere:\s*(\d+)/5", ratings_text)
                            
                            food_rating = food_match.group(1) if food_match else None
                            service_rating = service_match.group(1) if service_match else None
                            atmosphere_rating = atmosphere_match.group(1) if atmosphere_match else None
                    else:
                        review_text_element = review.locator('div.gyKkFe.JhRJje.Fv38Af')
                        if review_text_element.count() > 0:
                            review_text = review_text_element.inner_text()

                    # Images
                    images = review.locator('img.T3g1hc')
                    image_urls = [img.get_attribute('src') for img in images.all() if img.get_attribute('src')]
                    
                    # Append data to list
                    reviews_data.append({
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
                    })
                
                except Exception as e:
                    print(f"Error extracting review {i+1}: {e}")

            print(f"Extracted details for {len(reviews_data)} reviews")

            # Convert the list of reviews into a pandas DataFrame
            reviews_df = pd.DataFrame(reviews_data)
            
            # Save to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'reviews_{timestamp}.csv'
            reviews_df.to_csv(filename, index=False)

            print(f"Reviews successfully extracted and saved to {filename}!")
            return len(reviews_data), filename
  
        except Exception as e:
            print(f"Error in collect_reviews: {e}")
            # Take a screenshot when an error occurs
            page.screenshot(path="error_screenshot.png")
            return 0, None  # Return defaults if there's an error
        
        finally:
            browser.close()


if __name__ == "__main__":
    count, filename = collect_reviews()
    if count > 0:
        print(f"\nSuccessfully extracted {count} reviews and saved to {filename}")
    else:
        print("\nNo reviews were extracted - check error screenshot")