-- Paati Veedu Reviews Database Schema
-- Drop existing tables if they exist
DROP TABLE IF EXISTS review_responses;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS processing_logs;

-- Reviews table - stores all scraped reviews
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    review_id TEXT UNIQUE NOT NULL,  -- Google's unique review ID
    listing_id TEXT NOT NULL,        -- Google My Business listing ID
    reviewer_name TEXT NOT NULL,
    reviewer_profile_url TEXT,
    is_local_guide BOOLEAN DEFAULT FALSE,
    review_count INTEGER,
    photo_count INTEGER,
    rating INTEGER NOT NULL,         -- 1-5 stars
    review_time TEXT NOT NULL,       -- Original time string from Google
    review_text TEXT,
    share_url TEXT,
    dine_in TEXT,
    session TEXT,
    price_range TEXT,
    food_rating INTEGER,
    service_rating INTEGER,
    atmosphere_rating INTEGER,
    images TEXT[],                   -- Array of image URLs
    has_response BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Review responses table - stores AI-generated responses
CREATE TABLE review_responses (
    id SERIAL PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    response_text TEXT NOT NULL,
    sentiment TEXT,                  -- positive, negative, neutral
    issues TEXT,                     -- Identified issues from the review
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    posted_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'generated', -- generated, posted, failed
    post_attempts INTEGER DEFAULT 0,
    last_error TEXT
);

-- Processing logs table - tracks automation runs
CREATE TABLE processing_logs (
    id SERIAL PRIMARY KEY,
    process_type TEXT NOT NULL,      -- 'collection', 'generation', 'posting'
    status TEXT NOT NULL,            -- 'started', 'completed', 'failed'
    reviews_processed INTEGER DEFAULT 0,
    responses_generated INTEGER DEFAULT 0,
    responses_posted INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB                   -- Additional process-specific data
);

-- Indexes for performance
CREATE INDEX idx_reviews_review_id ON reviews(review_id);
CREATE INDEX idx_reviews_has_response ON reviews(has_response);
CREATE INDEX idx_reviews_created_at ON reviews(created_at DESC);
CREATE INDEX idx_review_responses_review_id ON review_responses(review_id);
CREATE INDEX idx_review_responses_status ON review_responses(status);
CREATE INDEX idx_processing_logs_process_type ON processing_logs(process_type);
CREATE INDEX idx_processing_logs_started_at ON processing_logs(started_at DESC);

-- Enable Row Level Security (RLS) for better security
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role full access
CREATE POLICY "Service role can access all reviews" ON reviews
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all responses" ON review_responses
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can access all logs" ON processing_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();