from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time
import random

# Load environment variables
load_dotenv()

def login_google():
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
            page.wait_for_url('https://myaccount.google.com/?pli=1', timeout=30000)
            print("Login successful!")
            
            # Short delay before navigating to desired URL
            time.sleep(5)
            page.goto('https://g.co/kgs/HgU3VjS', timeout=60000)
            
            # Handle "Not Now" button
            try:
                not_now_button = page.locator('g-raised-button:has-text("Not now")')
                not_now_button.click()
                print("Clicked 'Not Now' button.")
            except Exception:
                print("Could not find or click 'Not Now' button.")
            
            print("Successfully navigated!")
            input("Press Enter to close the browser...")
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    login_google()
