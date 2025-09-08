from anthropic import Anthropic
import os
import json
import re

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_response(review_text, rating, reviewer_name=None, model_name="claude-3-sonnet-20240229"):
    # Ensure reviewer_name is not None
    reviewer_name = reviewer_name if reviewer_name else "Guest"
    
    # Escape special characters in inputs to prevent JSON issues
    review_text = review_text.replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
    reviewer_name = reviewer_name.replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
    
    prompt = f"""
    You are an AI assistant for *Paati Veedu*, a fine-dining South Indian vegetarian restaurant in Chennai. Your task is to:
    1. Generate a response to the review as the restaurant’s owner: warm, personal, gracious, and human.
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
    ```json
    {{
        "response_text": "Dear <reviewer_name>, ... Regards",
        "sentiment": "<sentiment>",
        "issues": "<issues>"
    }}
    ```
    Ensure the JSON is valid, with no unescaped control characters (e.g., newlines, tabs) in `response_text`.

    **Examples**:
    Example 1:
    <customer_review>Loved the food, but service was slow.</customer_review>
    <rating>4</rating>
    <reviewer_name>Priya</reviewer_name>
    Output:
    ```json
    {{
        "response_text": "Dear Priya,\\nThank you for your kind words about our food! We're sorry for the slow service and will address this to ensure a better experience next time. Please visit us again soon!\\nRegards",
        "sentiment": "Positive",
        "issues": "Poor Service"
    }}
    ```

    Example 2:
    <customer_review>Overpriced and tasteless food.</customer_review>
    <rating>2</rating>
    <reviewer_name>Anil</reviewer_name>
    Output:
    ```json
    {{
        "response_text": "Dear Anil,\\nWe’re truly sorry to hear about your experience. Your feedback about pricing and taste is noted, and we’ll work to improve. Please give us another chance to serve you better.\\nRegards",
        "sentiment": "Do not like us",
        "issues": "Too expensive, Taste"
    }}
    ```

    Now, process the following:

    <customer_review>
    {review_text}
    </customer_review>

    <rating>
    {rating}
    </rating>

    <reviewer_name>
    {reviewer_name}
    </reviewer_name>
    """

    model_config = {
        "claude-3-sonnet-20240229": {"max_tokens": 600, "temperature": 0.7},
        "claude-3-haiku-20240307": {"max_tokens": 400, "temperature": 0.7}
    }

    model_params = model_config.get(model_name, model_config["claude-3-sonnet-20240229"])

    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=model_params["max_tokens"],
            temperature=model_params["temperature"],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract and parse the response
        try:
            full_content = response.content[0].text
            print(f"Raw API response: {full_content}")  # Debug raw output
            
            # Look for JSON block
            json_start = full_content.find("```json")
            json_end = full_content.rfind("```")
            
            if json_start == -1 or json_end == -1:
                # Fallback: Try to find JSON-like content without code block
                json_match = re.search(r'\{.*?\}', full_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("JSON block or valid JSON not found")
            else:
                json_str = full_content[json_start + 7:json_end].strip()
            
            # Clean JSON string (remove unescaped control characters)
            json_str = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
            result = json.loads(json_str)
            
            # Validate required fields
            if not all(key in result for key in ["response_text", "sentiment", "issues"]):
                raise ValueError("Missing required fields in JSON")
            
            # Ensure response_text starts with correct reviewer_name
            if not result["response_text"].startswith(f"Dear {reviewer_name},"):
                result["response_text"] = f"Dear {reviewer_name},\n" + result["response_text"]
            
            print(f"generate_response output: {result}")
            return {
                "success": True,
                "response": result["response_text"],
                "sentiment": result["sentiment"],
                "issues": result["issues"],
                "error": None
            }
        except Exception as e:
            result = {
                "success": False,
                "response": None,
                "sentiment": None,
                "issues": None,
                "error": f"Error parsing response: {str(e)}"
            }
            print(f"generate_response error: {result}")
            return result
            
    except Exception as e:
        result = {
            "success": False,
            "response": None,
            "sentiment": None,
            "issues": None,
            "error": f"Error generating response: {str(e)}"
        }
        print(f"generate_response error: {result}")
        return result