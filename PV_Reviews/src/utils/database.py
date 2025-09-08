"""Database utilities for storing review data in SQLite."""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ReviewDatabase:
    """SQLite database manager for review data."""
    
    def __init__(self, db_path: str = "data/reviews.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id TEXT UNIQUE NOT NULL,
                    listing_id TEXT NOT NULL,
                    reviewer_name TEXT NOT NULL,
                    reviewer_profile_url TEXT,
                    is_local_guide BOOLEAN,
                    review_count REAL,
                    photo_count REAL,
                    rating TEXT NOT NULL,
                    time TEXT NOT NULL,
                    review_text TEXT,
                    share_url TEXT,
                    dine_in TEXT,
                    session TEXT,
                    price_range TEXT,
                    food_rating REAL,
                    service_rating REAL,
                    atmosphere_rating REAL,
                    images TEXT,  -- JSON array of image URLs
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    has_response BOOLEAN DEFAULT FALSE,
                    response_generated BOOLEAN DEFAULT FALSE,
                    response_posted BOOLEAN DEFAULT FALSE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS run_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date DATE NOT NULL,
                    reviews_collected INTEGER NOT NULL,
                    new_reviews INTEGER NOT NULL,
                    duration_seconds REAL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_review_id ON reviews(review_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collected_at ON reviews(collected_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_has_response ON reviews(has_response)")
    
    def save_reviews(self, reviews_data: List[Dict]) -> tuple[int, int]:
        """Save reviews to database, returning (total_saved, new_reviews)."""
        total_saved = 0
        new_reviews = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for review in reviews_data:
                try:
                    # Convert images list to JSON string
                    images_json = json.dumps(review.get('Images', []))
                    
                    cursor = conn.execute("""
                        INSERT OR IGNORE INTO reviews (
                            review_id, listing_id, reviewer_name, reviewer_profile_url,
                            is_local_guide, review_count, photo_count, rating, time,
                            review_text, share_url, dine_in, session, price_range,
                            food_rating, service_rating, atmosphere_rating, images
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(review.get('Review ID', '')),
                        str(review.get('Listing ID', '')),
                        str(review.get('Reviewer Name', '')),
                        str(review.get('Reviewer Profile URL', '')),
                        bool(review.get('Is Local Guide', False)),
                        float(review.get('Review Count', 0)) if review.get('Review Count') is not None else None,
                        float(review.get('Photo Count', 0)) if review.get('Photo Count') is not None else None,
                        str(review.get('Rating', '')),
                        str(review.get('Time', '')),
                        str(review.get('Review Text', '')),
                        str(review.get('Share URL', '')),
                        str(review.get('Dine In', '')),
                        str(review.get('Session', '')),
                        str(review.get('Price Range', '')),
                        float(review.get('Food Rating', 0)) if review.get('Food Rating') is not None else None,
                        float(review.get('Service Rating', 0)) if review.get('Service Rating') is not None else None,
                        float(review.get('Atmosphere Rating', 0)) if review.get('Atmosphere Rating') is not None else None,
                        images_json
                    ))
                    
                    if cursor.rowcount > 0:
                        new_reviews += 1
                    total_saved += 1
                    
                except sqlite3.Error as e:
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