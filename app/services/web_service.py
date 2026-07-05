import logging

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

logger = logging.getLogger(__name__)

class WebService:
    
    @staticmethod
    def scrape_url(url: str) -> str:
        """
        Fetches the HTML from a URL and extracts clean, readable text.
        Strips out scripts, styles, navigation, and headers.
        """
        if not requests or not BeautifulSoup:
            logger.error("Dependencies missing. Run `pip install requests beautifulsoup4`")
            return "Error: Missing dependencies. Please install requests and beautifulsoup4."

        try:
            # Set a user-agent to avoid getting blocked by basic anti-bot filters
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove invisible and structural elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.extract()
                
            # Extract text, joining with a single space
            text = soup.get_text(separator=' ')
            
            # Clean up excessive whitespace
            clean_text = " ".join(text.split())
            
            if not clean_text:
                return "Error: Could not extract any readable text from this URL."
                
            return clean_text
            
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            return f"Error: Could not fetch content from URL. ({str(e)})"
