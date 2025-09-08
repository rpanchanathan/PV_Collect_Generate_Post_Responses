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
# Added logic to handle 'More Reviews' button until all reviews are processed.
def handle_more_reviews(page):
    while True:
        try:
            more_reviews_button = page.query_selector('button[aria-label="More Reviews"]')
            if more_reviews_button:
                more_reviews_button.click()
                time.sleep(2)  # Allow time for new reviews to load
            else:
                break  # Exit the loop if the button is not found
        except Exception as e:
            print(f"Error clicking 'More Reviews': {e}")
            break

MAX_REVIEWS = 20  # Adjust based on daily volume
OUTPUT_DIR = "/Users/rajeshpanchanathan/Library/CloudStorage/GoogleDrive-rajesh@genwise.in/My Drive/PV/Auto_Review_Response"

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
        
        # Handle 'More Reviews' button to load all reviews
        handle_more_reviews(page)
        
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
            except Exception as e:
                print(f"Could not click 'Unreplied' button inside iframe: {e}")
            
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
            total_reviews = 0

            # Loop through each review
            for review in review_elements:
                try:
                    # Extract unique identifiers
                    review_id = review.locator('div.KuKPRc').get_attribute('data-review-id')
                    listing_id = review.locator('div.KuKPRc').get_attribute('data-listing-id')
                    share_url = review.locator('div.KuKPRc').get_attribute('data-share-review-url')

                    # Extract reviewer name, and other details
                    reviewer_name = review.locator('a.PskQHd[jsname="xs1xe"]').inner_text()
                    reviewer_profile_url = review.locator('a.PskQHd[aria-label*="Link to reviewer profile"]').get_attribute('href')
                    reviewer_details = get_element_text(review, 'div.PROnRd.vq72z')  # e.g., "Local Guide • 36 reviews • 7 photos"
                    
                    # Parse reviewer details
                    is_local_guide = "Local Guide" in reviewer_details
                    review_count = None
                    photo_count = None
                    if "reviews" in reviewer_details:
                        review_count = int(re.search(r"(\d+)\s+reviews", reviewer_details).group(1))
                    if "photos" in reviewer_details:
                        photo_count = int(re.search(r"(\d+)\s+photos", reviewer_details).group(1))
                    
                    # Extract review rating (count the number of stars)
                    stars_element = review.locator('span[role="img"]')
                    review_rating = stars_element.get_attribute('aria-label') if stars_element else "No rating"
                    
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
                    if full_review_btn.is_visible():
                        full_review_btn.click()
                        review_text = review.locator('div[jsname="PBWx0c"]').inner_text()
                        ratings_text = review.locator('div.fjB0Xb').inner_text()
                        food_rating = re.search(r"Food:\s*(\d+)/5", ratings_text).group(1) if "Food" in ratings_text else None
                        service_rating = re.search(r"Service:\s*(\d+)/5", ratings_text).group(1) if "Service" in ratings_text else None
                        atmosphere_rating = re.search(r"Atmosphere:\s*(\d+)/5", ratings_text).group(1) if "Atmosphere" in ratings_text else None
                    else:
                        review_text = review.locator('div.gyKkFe.JhRJje.Fv38Af').inner_text()

                    # Images
                    images = review.locator('img.T3g1hc')
                    image_urls = [img.get_attribute('src') for img in images.all() if img.get_attribute('src')]
                    
                    # Extract review text
                    # review_text = review.locator('div.fjB0Xb').inner_text() if full_review_btn.count() > 0 else review.locator('div.dGCoId').inner_text()
                    
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
                    print(f"Error extracting review: {e}")

                total_reviews += 1
                if total_reviews > len(review_elements):
                    break


            # Convert the list of reviews into a pandas DataFrame
            reviews_df = pd.DataFrame(reviews_data)
            print(reviews_df)
            # Save to CSV if needed
            reviews_df.to_csv('reviews.csv', index=False)

            print("Reviews successfully extracted and saved!")
  
        except Exception as e:
            print(f"Error in collect_reviews: {e}")
            return 0, None  # Return defaults if there's an error
        
        finally:
            browser.close()
    
        return total_reviews, "reviews.csv"


if __name__ == "__main__":
    count, filename = collect_reviews()
    if count > 0:
        print(f"\nSuccessfully extracted {count} reviews")
    else:
        print("\nNo reviews were extracted - check error screenshot")