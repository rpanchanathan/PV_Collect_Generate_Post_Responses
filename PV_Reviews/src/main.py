import os
import pandas as pd
from datetime import datetime, timedelta
from Generate_Responses import generate_response
from anthropic import Anthropic
import re

# Initialize API client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Function to parse relative and absolute time formats
def parse_review_time(time_str, reference_date=datetime.now()):
    if pd.isna(time_str):
        return pd.NaT
    
    time_str = time_str.strip().lower()
    
    # Handle relative times
    if 'ago' in time_str:
        num = re.search(r'(\d+)', time_str)
        if not num:
            return pd.NaT
        num = int(num.group(1))
        
        if 'hour' in time_str:
            return reference_date - timedelta(hours=num)
        elif 'day' in time_str:
            return reference_date - timedelta(days=num)
        elif 'week' in time_str:
            return reference_date - timedelta(weeks=num)
        elif 'month' in time_str:
            return reference_date - timedelta(days=num * 30)  # Approximate
    elif 'yesterday' in time_str:
        return reference_date - timedelta(days=1)
    
    # Handle absolute dates (e.g., "11 Feb 2024")
    try:
        return pd.to_datetime(time_str, errors='coerce')
    except:
        return pd.NaT

# Load reviews CSV
csv_path = "reviews_latest.csv"
try:
    df = pd.read_csv(csv_path)
    print(f"Initial DataFrame shape: {df.shape}")
except FileNotFoundError:
    print(f"Error: CSV file {csv_path} not found")
    exit(1)

# Rename columns for consistency
df.rename(columns={
    'Rating': 'rating',
    'Review Text': 'review_text',
    'Reviewer Name': 'reviewer_name',
    'Time': 'review_time'
}, inplace=True)

# Inspect review_time values
print("\nSample review_time values:")
print(df['review_time'].head(10))
print(f"Unique review_time values (first 20): {df['review_time'].unique()[:20]}")

# Convert review_time to datetime
cutoff_date = datetime.now() - timedelta(weeks=16)
df["review_time"] = df["review_time"].apply(parse_review_time)
print(f"\nShape after date conversion: {df.shape}")
print(f"NaT review_time count: {df['review_time'].isna().sum()}")

# Log rows with NaT values
nat_rows = df[df['review_time'].isna()]
if not nat_rows.empty:
    print("\nRows with NaT review_time (first 5):")
    print(nat_rows[['review_time', 'rating', 'review_text', 'reviewer_name']].head())

# Filter: reviews within last 16 weeks
df = df[df["review_time"] >= cutoff_date]
print(f"Shape after time filter: {df.shape}")

# Remove rows with missing ratings or names
df = df.dropna(subset=["rating", "reviewer_name"])
print(f"Shape after dropna: {df.shape}")

# Select rows 25 to 29 (5 reviews)
# df_subset = df.iloc[25:30]
df_subset = df
print(f"Shape of df_subset: {df_subset.shape}")

# Check if df_subset is empty
if df_subset.empty:
    print("Error: No reviews available after filtering or slicing. Check CSV data (dates, missing values).")
    print(f"Cutoff date: {cutoff_date}")
    exit(1)

# Generate responses, sentiment, and issues
def get_response_text(row):
    result = generate_response(
        review_text=row["review_text"] if pd.notna(row["review_text"]) else "",
        rating=str(row["rating"]),
        reviewer_name=row["reviewer_name"]
    )
    print("\n---\n")
    print(f"⭐ {row['rating']} by {row['reviewer_name']} on {row['review_time'].date()}\n")
    print(f"Result from generate_response: {result}")
    print("\n---\n")
    if result["success"]:
        return {
            "response_text": result["response"].strip(),
            "sentiment": result["sentiment"],
            "issues": result["issues"]
        }
    return {
        "response_text": f"Error: {result['error']}",
        "sentiment": "Unknown",
        "issues": "None"
    }

df_subset = df_subset.copy()
# Apply response generation and extract sentiment/issues
results = df_subset.apply(get_response_text, axis=1)
df_subset["response_text"] = results.apply(lambda x: x["response_text"]).astype(str)
df_subset["Sentiment"] = results.apply(lambda x: x["sentiment"])
df_subset["Issue(s)"] = results.apply(lambda x: x["issues"])

# Debug: Print df_subset with new columns
print("\nSelected df_subset with sentiment and issues:")
print(df_subset[['reviewer_name', 'rating', 'review_text', 'Sentiment', 'Issue(s)', 'response_text']])

# Save to CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"review_responses_{timestamp}.csv"
df_subset.to_csv(output_file, index=False)

print(f"\n✅ Responses saved to {output_file}")