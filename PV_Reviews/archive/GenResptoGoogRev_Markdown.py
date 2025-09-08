# %% [markdown]
# # Generate Suggested Responses to Google Reviews
# 
# ## Batch Processing (At Random)
# ## Using Different Models for Different Reviews

# %%
!pip install openpyxl

# %%
# Cell 1: Setup and Imports
import os
from dotenv import load_dotenv
import anthropic
import pandas as pd
from typing import Dict
import numpy as np
from openpyxl import load_workbook
from datetime import datetime
import time
from IPython.core.debugger import set_trace
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')
client = anthropic.Anthropic(api_key=API_KEY)

# %%
# Cell 2: Read Data (Modified) 
def extract_rating(rating_str):
    """Extract numeric rating from string like '4 out of 5 stars'"""
    try:
        # Extract first number from string
        rating = float(rating_str.split()[0])
        return rating
    except:
        return 5.0  # Default to 5 if parsing fails, we can discuss this default

def split_into_queues(df):
    
    # First ensure Review Text is string
    df['Review Text'] = df['Review Text'].astype(str)

    # Define queue conditions
    detailed_mask = (
        (df['Review Text'].str.len() > 50) |  # Long reviews
        (df['Rating'].apply(extract_rating) < 4)  # Negative reviews
    )
    
    # Split dataframes
    detailed_queue = df[detailed_mask].copy()
    standard_queue = df[~detailed_mask].copy()
    
    return detailed_queue, standard_queue

# Read Excel instead of CSV
df = pd.read_excel('reviews.xlsx')
# Convert Rating to numeric
df['Rating'] = df['Rating'].str.extract(r'(\d)').astype(float)

detailed_df, standard_df = split_into_queues(df)
print(f"Total reviews: {len(df)}")
print(f"Detailed queue: {len(detailed_df)}")
print(f"Standard queue: {len(standard_df)}")


# %%
# Cell 3: Generate Responses (Modified)

def generate_response(review_text: str, rating: str, reviewer_name: str = "", review_time=None) -> Dict:
    """Generate response using appropriate model based on review type"""

    logger.info(f"""
    Attempting to process:
    Review: '{review_text}'
    Rating: '{rating}'
    Name: '{reviewer_name}'
    """)

    # Input validation
    if pd.isna(review_text) or pd.isna(rating):
        return {
            "success": False,
            "response": None,
            "error": "Missing required review text or rating"
        }
    
    # Convert review_text to string if not already
    review_text = str(review_text)

    # Determine if review needs detailed handling
    try:
        numeric_rating = extract_rating(rating)        
        is_detailed = (
            len(review_text) > 50 or 
            numeric_rating < 4
        )
    except ValueError:
        return {
            "success": False,
            "response": None,
            "error": "Invalid rating format"
        }

    # Log which model is being used
    logger.info(f"Using {'detailed' if is_detailed else 'standard'} queue")

    # Select model configuration
    if is_detailed:
        model_config = {
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.75,
            "max_tokens": 800
        }
    else:
        model_config = {
            "model": "claude-3-haiku-20240307",
            "temperature": 0.6,
            "max_tokens": 700
        }
    
    try:    
        prompt = f"""You are an AI assistant responding on behalf of Paati Veedu, a fine dining vegetarian restaurant in Chennai. Your task is to generate professional and warm responses to customer reviews while maintaining consistency in tone and brand voice.

IMPORTANT: YOUR ENTIRE RESPONSE MUST BE IN THIS FORMAT:

<response>
Dear {reviewer_name if reviewer_name else "Valued Guest"},

[Your complete response here]

The Paati Veedu Team
</response>

Here is the customer's review:
<customer_review>
{review_text}
</customer_review>

Here is the rating they provided:
<customer_rating>
{rating}
</customer_rating>

Here is the reviewer's name:
<reviewer_name>
{reviewer_name}
</reviewer_name>

Before crafting your response, please analyze the review and consider the following points. Wrap your analysis in <review_analysis> tags:

1. Identify the overall sentiment of the review (positive, negative, or mixed).
2. Categorize the rating (excellent, good, average, poor).
3. List any specific aspects of the dining experience mentioned by the customer (e.g., food quality, service, ambiance, specific dishes).
4. Note any particular praise or concerns expressed in the review.
5. Consider how to address each point while maintaining a professional and warm tone.
6. Think about how to genuinely appreciate the customer's feedback without sounding generic.
7. Plan how to incorporate Paati Veedu's brand voice as a fine dining vegetarian restaurant in your response.
8. Consider the cultural context of Chennai and how it might influence your response.

Now, based on your analysis, craft a response to the customer review (between <response> tags).Your response should:

1. Begin with a warm greeting and genuine appreciation for the customer's feedback.
2. Address specific points mentioned in the review, demonstrating that you've carefully read and considered their comments.
3. If the review is positive, express gratitude and reinforce the positive aspects.
4. If the review includes any concerns or negative feedback, acknowledge them respectfully and provide a thoughtful response or solution (if possible).
5. Maintain a professional yet warm tone throughout, consistent with Paati Veedu's brand as a fine dining establishment.
6. Conclude with an invitation for the customer to return and enjoy another dining experience at Paati Veedu.
7. Format response as a well-structured paragraph or two, suitable for a direct reply to the customer's review. Aim for a concise and engaging reply. 4 and 5 stars need no more than 50-60 words; poorer ratings, supported by detailed reviews could be longer.
8. Always sign-off as "The Paati Veedu Team".
9. Even for short or missing reviews, acknowledge the rating and invite them back.
"""

        
        logger.info(f"Full prompt being sent: {prompt}")
        
        # Rate limiting
        time.sleep(1)  # Basic rate limiting

        message = client.messages.create(
            model=model_config["model"],
            max_tokens=model_config["max_tokens"],
            temperature=model_config["temperature"],
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        )
        
        # Debugging: Log or print the full API response content
        print("\nFull API Response Content:")
        print(message.content)
                
        # Extract only the response section with error handling
        try:
            full_content = message.content[0].text
            response_start = full_content.find("<response>") + len("<response>")
            response_end = full_content.find("</response>")
            
            if response_start == -1 or response_end == -1:
                raise ValueError("Response tags not found")
                
            response_text = full_content[response_start:response_end].strip()
            
            if not response_text:
                raise ValueError("Empty response")
                
            return {
                "success": True,
                "response": response_text,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": f"Error parsing response: {str(e)}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "error": f"API Error: {str(e)}"
        }

# %%
# Cell 4: Batch Processing with Interactive Control

def process_batch(batch_df, batch_num, total_batches):
    """Process a single batch of reviews"""
    responses = []
    for idx, row in batch_df.iterrows():
        print(f"Processing review {idx + 1} in batch {batch_num}/{total_batches}")
        
        result = generate_response(
            review_text=row['Review Text'],
            rating=row['Rating'],
            reviewer_name=row['Reviewer Name'].strip() if pd.notna(row['Reviewer Name']) else '',
            review_time=row['Time']
        )
        responses.append(result['response'] if result['success'] else f"Error: {result['error']}")
    
    batch_df['Suggested_Response'] = responses
    return batch_df

def process_reviews(detailed_df, standard_df, batch_size=50, auto_mode=False):
    """Process all reviews with optional automatic mode"""
    
    # Combine and shuffle both queues
    detailed_df['queue'] = 'detailed'
    standard_df['queue'] = 'standard'
    all_df = pd.concat([detailed_df, standard_df]).sample(frac=1).reset_index(drop=True)
    
    # Calculate total batches
    total_batches = len(all_df) // batch_size + (1 if len(all_df) % batch_size else 0)
    processed_dfs = []
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = start_idx + batch_size
        batch_df = all_df.iloc[start_idx:end_idx].copy()
        
        # Process batch
        processed_batch = process_batch(batch_df, batch_num + 1, total_batches)
        processed_dfs.append(processed_batch)
        
        # Save intermediate results
        interim_df = pd.concat(processed_dfs)
        interim_df.to_excel(f'reviews_with_responses_batch_{batch_num + 1}.xlsx', index=False)
        
        # Interactive control if not in auto mode
        print(f"\nBatch {batch_num + 1}/{total_batches} completed")
        print(f"Results saved to reviews_with_responses_batch_{batch_num + 1}.xlsx")
        
        if not auto_mode and batch_num < total_batches - 1:  # Don't ask after last batch
            while True:
                choice = input("\nEnter 'c' to continue to next batch, or 'x' to exit: ").lower()
                if choice in ['c', 'x']:
                    break
            
            if choice == 'x':
                print("Processing stopped after batch", batch_num + 1)
                break
    
    # Combine all processed batches
    final_df = pd.concat(processed_dfs)
    final_df.to_excel('reviews_with_responses_final.xlsx', index=False)
    return final_df

# %%
# Cell 5: Execute Batch Processing with Interactive Control
def main():
    # Read and split data
    df = pd.read_excel('reviews.xlsx')
    detailed_df, standard_df = split_into_queues(df)
    
    print("\nInitial Data Summary:")
    print(f"Total reviews: {len(df)}")
    print(f"Detailed queue: {len(detailed_df)}")
    print(f"Standard queue: {len(standard_df)}")
    
    # Confirm before starting
    while True:
        start = input("\nEnter 'y' to start processing, 'n' to exit: ").lower()
        if start in ['y', 'n']:
            break
    
    if start == 'n':
        print("Program terminated before processing")
        return

    # Ask for processing mode
    while True:
        mode = input("\nEnter processing mode:\n'i' for interactive (review after each batch)\n'a' for automatic (process all batches)\nYour choice: ").lower()
        if mode in ['i', 'a']:
            break
    
    try:
        # Process reviews in batches
        processed_df = process_reviews(detailed_df, standard_df, batch_size=50, auto_mode=(mode == 'a'))
        
        print("\nProcessing Complete!")
        print(f"Total reviews processed: {len(processed_df)}")
        print("Final results saved to 'reviews_with_responses_final.xlsx'")
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    except Exception as e:
        print(f"\nError during processing: {str(e)}")
    finally:
        print("\nProgram execution completed")

# Execute if running directly
if __name__ == "__main__":
    main()
