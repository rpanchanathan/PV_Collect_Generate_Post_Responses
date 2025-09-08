"""Configuration settings for PV Reviews automation."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Application configuration."""
    
    # Authentication
    google_email: str = os.getenv('GOOGLE_EMAIL', '')
    google_password: str = os.getenv('GOOGLE_PASSWORD', '')
    anthropic_api_key: str = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Database Configuration
    supabase_url: str = os.getenv('SUPABASE_URL', '')
    supabase_anon_key: str = os.getenv('SUPABASE_ANON_KEY', '')
    supabase_service_key: str = os.getenv('SUPABASE_SERVICE_KEY', '')
    use_database: bool = True  # Switch between CSV and database modes
    
    # Business Details
    business_listing_id: str = "11382416837896137085"
    business_url: str = "https://g.co/kgs/HgU3VjS"
    
    # Browser Settings
    headless: bool = False  # Google auth requires visible browser
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # Data Settings  
    data_dir: Path = Path(__file__).parent.parent / "data"
    max_reviews: int = 1000  # Increased to collect all reviews
    batch_size: int = 25
    batch_delay_mins: int = 15
    
    # Response Generation
    claude_model: str = "claude-3-5-sonnet-20241022"
    response_max_tokens: int = 600
    response_temperature: float = 0.7
    
    # Time Filters
    review_cutoff_weeks: int = 16

    def __post_init__(self):
        """Ensure data directory exists."""
        self.data_dir.mkdir(exist_ok=True)

# Global config instance
config = Config()