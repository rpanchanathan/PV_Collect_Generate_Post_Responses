"""Database utilities for storing review data in Supabase PostgreSQL."""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ReviewDatabase:
    """Supabase PostgreSQL database manager for review data."""
    
    def __init__(self):
        load_dotenv()
        self.url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.service_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")
        
        self.client = create_client(self.url, self.service_key)
    
    
    def save_reviews(self, reviews_data: List[Dict]) -> tuple[int, int]:
        """Save reviews to database, returning (total_saved, new_reviews)."""
        total_saved = 0
        new_reviews = 0
        
        for review in reviews_data:
            try:
                # Clean and validate review data
                cleaned_review = self._clean_review_data(review)
                if not cleaned_review:
                    continue
                
                # Try to insert, if exists it will update
                result = self.client.table('reviews').upsert(cleaned_review).execute()
                
                if result.data:
                    new_reviews += 1  # Simplified: counting all as new
                total_saved += 1
                    
            except Exception as e:
                logger.error(f"Error saving review {review.get('Review ID', 'Unknown')}: {e}")
        
        return total_saved, new_reviews
    
    def log_run(self, run_date: str, reviews_collected: int, new_reviews: int, 
                duration_seconds: float, status: str, error_message: str = None) -> None:
        """Log a collection run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO run_logs (run_date, reviews_collected, new_reviews, 
                                    duration_seconds, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (run_date, reviews_collected, new_reviews, duration_seconds, status, error_message))
    
    def get_unreplied_reviews(self, limit: Optional[int] = None) -> List[Dict]:
        """Get reviews that haven't been replied to."""
        query = """
            SELECT * FROM reviews 
            WHERE has_response = FALSE 
            ORDER BY collected_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_response_generated(self, review_ids: List[str]) -> None:
        """Mark reviews as having responses generated."""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(review_ids))
            conn.execute(f"""
                UPDATE reviews 
                SET response_generated = TRUE 
                WHERE review_id IN ({placeholders})
            """, review_ids)
    
    def mark_response_posted(self, review_ids: List[str]) -> None:
        """Mark reviews as having responses posted."""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(review_ids))
            conn.execute(f"""
                UPDATE reviews 
                SET response_posted = TRUE, has_response = TRUE 
                WHERE review_id IN ({placeholders})
            """, review_ids)
    
    def get_run_summary(self, days: int = 7) -> Dict:
        """Get summary of recent runs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get recent runs
            recent_runs = conn.execute("""
                SELECT * FROM run_logs 
                WHERE created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
            """.format(days)).fetchall()
            
            # Get total stats
            total_reviews = conn.execute("SELECT COUNT(*) as count FROM reviews").fetchone()['count']
            unreplied_reviews = conn.execute("SELECT COUNT(*) as count FROM reviews WHERE has_response = FALSE").fetchone()['count']
            
            return {
                'recent_runs': [dict(row) for row in recent_runs],
                'total_reviews': total_reviews,
                'unreplied_reviews': unreplied_reviews
            }