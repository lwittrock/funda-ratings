-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Properties table
CREATE TABLE properties (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  city TEXT,
  neighbourhood TEXT,
  postcode TEXT,
  province TEXT,
  price INTEGER,
  living_area INTEGER,
  plot_area INTEGER,
  bedrooms INTEGER,
  rooms INTEGER,
  construction_year INTEGER,
  energy_label TEXT,
  object_type TEXT,
  house_type TEXT,
  features JSONB DEFAULT '{}',
  thumbnail_url TEXT,
  funda_url TEXT,
  added_date TIMESTAMPTZ,
  last_seen TIMESTAMPTZ,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'removed')),
  removed_date TIMESTAMPTZ,
  price_history JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ratings table
CREATE TABLE ratings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id TEXT REFERENCES properties(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'unreviewed' CHECK (status IN ('unreviewed', 'rejected', 'reviewed', 'viewing_interest')),
  location_score INTEGER CHECK (location_score >= 0 AND location_score <= 5),
  house_quality_score INTEGER CHECK (house_quality_score >= 0 AND house_quality_score <= 5),
  garden_score INTEGER CHECK (garden_score >= 0 AND garden_score <= 5),
  value_score INTEGER CHECK (value_score >= 0 AND value_score <= 5),
  notes TEXT DEFAULT '',
  rejection_reason TEXT,
  reviewed_date TIMESTAMPTZ,
  updated_date TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(property_id)
);

-- Index for faster queries
CREATE INDEX idx_properties_status ON properties(status);
CREATE INDEX idx_properties_last_seen ON properties(last_seen DESC);
CREATE INDEX idx_ratings_property_id ON ratings(property_id);
CREATE INDEX idx_ratings_status ON ratings(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for properties
CREATE TRIGGER update_properties_updated_at
  BEFORE UPDATE ON properties
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for ratings
CREATE TRIGGER update_ratings_updated_at
  BEFORE UPDATE ON ratings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Since this is single-user, disable RLS for simplicity
-- (Enable RLS later if you add authentication)
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for single user (no auth required)
-- WARNING: This allows anyone with your anon key to read/write
-- Fine for personal projects, but add auth for production
CREATE POLICY "Allow all access to properties" ON properties
  FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all access to ratings" ON ratings
  FOR ALL USING (true) WITH CHECK (true);