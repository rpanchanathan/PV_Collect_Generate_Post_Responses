# main.py
import os
import pandas as pd
from datetime import datetime, timedelta
from Generate_Responses import generate_response  # assumes your function is saved in Generate_Responses.py
from anthropic import Anthropic

# Initialize API client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Load reviews CSV
csv_path = "reviews_20250420_105531.csv"
df = pd.read_csv(csv_path)

# Rename columns for consistency
df.rename(columns={
    'Rating': 'rating',
    'Review Text': 'review_text',
    'Reviewer Name': 'reviewer_name',
    'Time': 'review_time'
}, inplace=True)

# Filter: reviews within last 16 weeks
cutoff_date = datetime.now() - timedelta(weeks=16)
df["review_time"] = pd.to_datetime(df["review_time"], errors="coerce")
df = df[df["review_time"] >= cutoff_date]

# Remove rows with missing ratings or names
df = df.dropna(subset=["rating", "reviewer_name"])

# Select 10 reviews
df_subset = df.head(10)

# Generate responses and collect results
def get_response_text(row):
    result = generate_response(
        review_text=row["review_text"] if pd.notna(row["review_text"]) else "",
        rating=str(row["rating"]),
        reviewer_name=row["reviewer_name"]
    )
    print("\n---\n")
    print(f"⭐ {row['rating']} by {row['reviewer_name']} on {row['review_time'].date()}\n")
    print(result)
    print("\n---\n")
    return result["response"] if isinstance(result, dict) and result.get("success") else "Error generating response"

df_subset = df_subset.copy()
df_subset["response_text"] = df_subset.apply(get_response_text, axis=1)

# Save to CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"review_responses_{timestamp}.csv"
df_subset.to_csv(output_file, index=False)

print(f"\n✅ Responses saved to {output_file}")
