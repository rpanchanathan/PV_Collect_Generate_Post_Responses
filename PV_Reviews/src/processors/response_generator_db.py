#!/usr/bin/env python3
"""
Database-integrated response generator for Paati Veedu reviews
Generates AI-powered responses and saves them to the database
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import re
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from anthropic import Anthropic
from dotenv import load_dotenv

from config.settings import config
from src.utils.database import ReviewDatabase
from src.utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

logger = setup_logging()

class ResponseGenerator:
    """AI-powered response generator using Anthropic Claude."""
    
    def __init__(self):
        self.client = Anthropic(api_key=config.anthropic_api_key)
        self.db = ReviewDatabase()
    
    def generate_response(self, review_text: str, rating: int, reviewer_name: str = None) -> Dict:
        """
        Generate a response using Claude AI
        
        Args:
            review_text: The review content
            rating: Rating (1-5 stars) 
            reviewer_name: Name of the reviewer
            
        Returns:
            Dict with success, response_text, sentiment, issues, and error fields
        """
        # Ensure reviewer_name is not None
        reviewer_name = reviewer_name if reviewer_name else "Guest"
        
        # Escape special characters in inputs to prevent JSON issues
        review_text_escaped = review_text.replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        reviewer_name_escaped = reviewer_name.replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        
        prompt = f"""
        You are an AI assistant for *Paati Veedu*, a fine-dining South Indian vegetarian restaurant in Chennai. Your task is to:
        1. Generate a response to the review as the restaurant's owner: warm, personal, gracious, and human.
        2. Classify the sentiment of the review based on the review text and rating.
        3. Identify specific issues mentioned in the review text.

        **Style Guide for Response**:
        - Address the guest by their name, exactly as provided in <reviewer_name>.
        - Start with "Dear <reviewer_name>," using the provided name.
        - Keep it brief (20–50 words for 4–5 star reviews, under 100 words otherwise).
        - Reference specifics from the review.
        - For negative feedback, acknowledge sincerely and offer a polite assurance.
        - End warmly, inviting them to visit again.
        - Sign off with "Regards".

        **Sentiment Classification**:
        - Analyze the review text and rating (1–5) to classify sentiment into one of:
          - Very Positive
          - Positive
          - Neutral
          - Have Issues
          - Do not like us
        - Consider cases where the rating and text tone differ (e.g., 5 stars with issues, 4 stars with strong support).

        **Issue Detection**:
        - Identify issues in the review text, choosing from:
          - Too expensive
          - Limited Portions
          - Poor Service
          - Taste
          - Other (e.g., ambiance, cleanliness, noise, parking)
        - Return issues as a comma-separated list (e.g., "Poor Service, Taste") or "None" if none are found.

        **Output Format**:
        Return a JSON object wrapped in ```json ... ``` with three fields:
        - "response_text": Your generated response
        - "sentiment": One of the sentiment classifications above
        - "issues": Comma-separated list of issues or "None"

        **Review to respond to**:
        <reviewer_name>{reviewer_name_escaped}</reviewer_name>
        <rating>{rating}/5 stars</rating>
        <review_text>{review_text_escaped}</review_text>
        """

        try:
            message = self.client.messages.create(
                model=config.claude_model,
                max_tokens=config.response_max_tokens,
                temperature=config.response_temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_content = message.content[0].text
            logger.debug(f"Raw Claude response: {response_content}")
            
            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            result = json.loads(json_match.group(1))
            
            # Validate required fields
            required_fields = ["response_text", "sentiment", "issues"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"Generated response for {reviewer_name}: {result['sentiment']}")
            return {
                "success": True,
                "response_text": result["response_text"],
                "sentiment": result["sentiment"], 
                "issues": result["issues"],
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error generating response for {reviewer_name}: {e}")
            return {
                "success": False,
                "response_text": None,
                "sentiment": None,
                "issues": None,
                "error": f"Error generating response: {str(e)}"
            }
    
    def process_unreplied_reviews(self, limit: Optional[int] = None) -> Dict:
        """
        Process all unreplied reviews and generate responses
        
        Args:
            limit: Maximum number of reviews to process
            
        Returns:
            Dict with processing statistics
        """
        logger.info("Starting response generation for unreplied reviews")
        
        # Log process start
        log_id = self.db.log_process_start('generation', {'limit': limit})
        
        try:
            # Get unreplied reviews from database
            unreplied_reviews = self.db.get_unreplied_reviews(limit=limit)
            logger.info(f"Found {len(unreplied_reviews)} unreplied reviews")
            
            if not unreplied_reviews:
                logger.info("No unreplied reviews found")
                if log_id:
                    self.db.log_process_complete(log_id, 0, 0)
                return {
                    'total_reviews': 0,
                    'responses_generated': 0,
                    'errors': 0,
                    'error_details': []
                }
            
            # Process each review
            responses_generated = 0
            errors = 0
            error_details = []
            
            for i, review in enumerate(unreplied_reviews):
                try:
                    logger.info(f"Processing review {i+1}/{len(unreplied_reviews)}: {review['reviewer_name']}")
                    
                    # Generate response
                    result = self.generate_response(
                        review_text=review.get('review_text', ''),
                        rating=review.get('rating', 5),
                        reviewer_name=review.get('reviewer_name', 'Guest')
                    )
                    
                    if result['success']:
                        # Save response to database
                        success = self.db.save_response(
                            review_id=review['review_id'],
                            response_text=result['response_text'],
                            sentiment=result['sentiment'],
                            issues=result['issues']
                        )
                        
                        if success:
                            responses_generated += 1
                            logger.info(f"✅ Generated response for {review['reviewer_name']}")
                        else:
                            errors += 1
                            error_msg = f"Failed to save response for {review['reviewer_name']}"
                            logger.error(error_msg)
                            error_details.append(error_msg)
                    else:
                        errors += 1
                        error_msg = f"Failed to generate response for {review['reviewer_name']}: {result['error']}"
                        logger.error(error_msg)
                        error_details.append(error_msg)
                
                except Exception as e:
                    errors += 1
                    error_msg = f"Error processing review from {review.get('reviewer_name', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    error_details.append(error_msg)
            
            # Log completion
            if log_id:
                self.db.log_process_complete(
                    log_id=log_id,
                    reviews_processed=len(unreplied_reviews),
                    responses_generated=responses_generated,
                    error_message='; '.join(error_details[:3]) if error_details else None
                )
            
            logger.info(f"Response generation completed: {responses_generated} generated, {errors} errors")
            
            return {
                'total_reviews': len(unreplied_reviews),
                'responses_generated': responses_generated,
                'errors': errors,
                'error_details': error_details
            }
            
        except Exception as e:
            logger.error(f"Error in response generation process: {e}")
            if log_id:
                self.db.log_process_complete(log_id, 0, 0, error_message=str(e))
            
            return {
                'total_reviews': 0,
                'responses_generated': 0,
                'errors': 1,
                'error_details': [str(e)]
            }

def main():
    """Main function for running response generation"""
    print("🤖 Paati Veedu Response Generator (Database Version)")
    print("=" * 50)
    
    generator = ResponseGenerator()
    
    # Process all unreplied reviews
    results = generator.process_unreplied_reviews()
    
    print(f"\n📊 Results:")
    print(f"   Reviews processed: {results['total_reviews']}")
    print(f"   Responses generated: {results['responses_generated']}")
    print(f"   Errors: {results['errors']}")
    
    if results['error_details']:
        print(f"\n❌ Errors encountered:")
        for error in results['error_details'][:5]:  # Show first 5 errors
            print(f"   - {error}")
        if len(results['error_details']) > 5:
            print(f"   ... and {len(results['error_details']) - 5} more errors")
    
    if results['responses_generated'] > 0:
        print(f"\n✅ Successfully generated {results['responses_generated']} responses!")
        print("🌐 View them at: https://gmsehvplczsarizikwum.supabase.co/project/default/editor")

if __name__ == '__main__':
    main()