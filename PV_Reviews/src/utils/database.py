"""Database utilities for storing review data in Supabase PostgreSQL."""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
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
        try:
            log_data = {
                'process_type': 'collection',
                'status': status,
                'reviews_processed': reviews_collected,
                'metadata': {
                    'run_date': run_date,
                    'new_reviews': new_reviews,
                    'duration_seconds': duration_seconds
                }
            }
            
            if error_message:
                log_data['error_message'] = error_message
            
            self.client.table('processing_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging run: {e}")
    
    def get_unreplied_reviews(self, limit: Optional[int] = None) -> List[Dict]:
        """Get reviews that haven't been replied to."""
        query = self.client.table('reviews').select('*').eq('has_response', False).order('created_at', desc=True)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    
    def mark_response_generated(self, review_ids: List[str]) -> None:
        """Mark reviews as having responses generated."""
        try:
            for review_id in review_ids:
                self.client.table('reviews').update({'has_response': True}).eq('review_id', review_id).execute()
        except Exception as e:
            logger.error(f"Error marking responses generated: {e}")
    
    def mark_response_posted(self, review_ids: List[str]) -> None:
        """Mark reviews as having responses posted."""
        try:
            for review_id in review_ids:
                # Update review
                self.client.table('reviews').update({'has_response': True}).eq('review_id', review_id).execute()
                
                # Update response status
                self.client.table('review_responses').update({
                    'status': 'posted',
                    'posted_at': datetime.utcnow().isoformat()
                }).eq('review_id', review_id).execute()
                
        except Exception as e:
            logger.error(f"Error marking responses posted: {e}")
    
    def get_run_summary(self, days: int = 7) -> Dict:
        """Get summary of recent runs."""
        try:
            # Get recent processing logs
            from_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            recent_runs_result = self.client.table('processing_logs').select('*').gte('started_at', from_date).order('started_at', desc=True).execute()
            
            # Get total stats
            total_reviews_result = self.client.table('reviews').select('count').execute()
            unreplied_result = self.client.table('reviews').select('count').eq('has_response', False).execute()
            
            return {
                'recent_runs': recent_runs_result.data if recent_runs_result.data else [],
                'total_reviews': len(total_reviews_result.data) if total_reviews_result.data else 0,
                'unreplied_reviews': len(unreplied_result.data) if unreplied_result.data else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting run summary: {e}")
            return {'recent_runs': [], 'total_reviews': 0, 'unreplied_reviews': 0}
    
    def save_response(self, review_id: str, response_text: str, sentiment: str = '', issues: str = '') -> bool:
        """Save a generated response for a review."""
        try:
            response_data = {
                'review_id': review_id,
                'response_text': response_text,
                'sentiment': sentiment,
                'issues': issues,
                'status': 'generated'
            }
            
            result = self.client.table('review_responses').insert(response_data).execute()
            
            if result.data:
                # Update the review to mark it as having a response
                self.client.table('reviews').update({'has_response': True}).eq('review_id', review_id).execute()
                return True
                
        except Exception as e:
            logger.error(f"Error saving response for review {review_id}: {e}")
            
        return False
    
    def get_pending_responses(self, limit: Optional[int] = None) -> List[Dict]:
        """Get responses that are ready to be posted."""
        query = self.client.table('review_responses').select(
            '*, reviews!inner(*)'
        ).eq('status', 'generated').order('generated_at', desc=True)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    
    def _clean_review_data(self, review: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and validate review data for database insertion."""
        # Must have review_id and reviewer_name
        review_id = str(review.get('Review ID', '')).strip()
        reviewer_name = str(review.get('Reviewer Name', '')).strip()
        
        if not review_id or not reviewer_name:
            return None
        
        # Clean and convert data types
        cleaned = {
            'review_id': review_id,
            'listing_id': str(review.get('Listing ID', '')).strip(),
            'reviewer_name': reviewer_name,
            'reviewer_profile_url': str(review.get('Reviewer Profile URL', '')).strip(),
            'is_local_guide': bool(review.get('Is Local Guide', False)),
            'review_count': self._safe_int(review.get('Review Count')),
            'photo_count': self._safe_int(review.get('Photo Count')),
            'rating': self._extract_rating(review.get('Rating', '')),
            'review_time': str(review.get('Time', '')).strip(),
            'review_text': str(review.get('Review Text', '')).strip(),
            'share_url': str(review.get('Share URL', '')).strip(),
            'dine_in': str(review.get('Dine In', '')).strip(),
            'session': str(review.get('Session', '')).strip(),
            'price_range': str(review.get('Price Range', '')).strip(),
            'food_rating': self._safe_int(review.get('Food Rating')),
            'service_rating': self._safe_int(review.get('Service Rating')),
            'atmosphere_rating': self._safe_int(review.get('Atmosphere Rating')),
            'images': review.get('Images', []) if isinstance(review.get('Images', []), list) else [],
            'has_response': bool(review.get('has_response', False))
        }
        
        # Rating is required
        if not cleaned['rating']:
            return None
            
        return cleaned
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None or value == '':
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
    
    def _extract_rating(self, rating_str):
        """Extract numeric rating from string like '5 out of 5 stars'"""
        if not rating_str:
            return None
        try:
            # Extract first number from string
            import re
            match = re.search(r'(\d+)', str(rating_str))
            return int(match.group(1)) if match else None
        except:
            return None
    
    def log_process_start(self, process_type: str, metadata: Dict[str, Any] = None) -> int:
        """Log the start of a process (collection, generation, posting)"""
        try:
            log_data = {
                'process_type': process_type,
                'status': 'started',
                'metadata': metadata or {}
            }
            
            result = self.client.table('processing_logs').insert(log_data).execute()
            return result.data[0]['id'] if result.data else None
            
        except Exception as e:
            logger.error(f"Error logging process start: {e}")
            return None
    
    def log_process_complete(self, log_id: int, reviews_processed: int = 0, 
                           responses_generated: int = 0, responses_posted: int = 0,
                           error_message: str = None) -> bool:
        """Log the completion of a process"""
        try:
            update_data = {
                'status': 'failed' if error_message else 'completed',
                'reviews_processed': reviews_processed,
                'responses_generated': responses_generated,
                'responses_posted': responses_posted,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            result = self.client.table('processing_logs').update(update_data).eq('id', log_id).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error logging process completion: {e}")
            return False