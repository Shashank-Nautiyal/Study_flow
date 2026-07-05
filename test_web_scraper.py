import os
import sys

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.web_service import WebService

def test_web_scraper():
    print("=== Testing Web Scraper Engine ===")
    
    # Use a standard text-heavy page (e.g., Python's official about page)
    test_url = "https://www.python.org/about/"
    
    print(f"Target URL: {test_url}")
    print("Initiating scraping...")
    
    try:
        scraped_text = WebService.scrape_url(test_url)
        
        # Only print the first 500 characters to keep output clean
        preview = scraped_text[:500] + "..." if len(scraped_text) > 500 else scraped_text
        
        print("\n--- Scraper Result (Preview) ---")
        print(preview)
        print("\n--------------------------------")
        
        if scraped_text and not scraped_text.startswith("Error"):
            print("SUCCESS: Web scraper engine works and extracted text!")
            print(f"Total extracted length: {len(scraped_text)} characters")
        else:
            print("FAILED: Did not get valid text back.")
            print(f"Error output: {scraped_text}")
            
    except Exception as e:
        print(f"FAILED: Exception occurred during testing: {e}")

if __name__ == "__main__":
    test_web_scraper()
