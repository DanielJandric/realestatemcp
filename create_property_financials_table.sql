-- Add financial and technical columns to properties table
-- Plus create separate valuations table for multiple appraisals

-- First, add columns to properties table
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS purchase_price NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS purchase_date DATE,
ADD COLUMN IF NOT EXISTS construction_year INTEGER,
ADD COLUMN IF NOT EXISTS renovation_year INTEGER,
ADD COLUMN IF NOT EXISTS renovation_type TEXT,
ADD COLUMN IF NOT EXISTS heating_type TEXT,
ADD COLUMN IF NOT EXISTS heating_fuel TEXT,
ADD COLUMN IF NOT EXISTS mortgage_amount NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS annual_rental_income NUMERIC(12,2);

-- Create valuations table for multiple appraisals
DROP TABLE IF EXISTS property_valuations CASCADE;

CREATE TABLE property_valuations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    valuation_date DATE NOT NULL,
    valuation_source TEXT NOT NULL, -- 'CBRE', 'Cronos', 'Beausire', 'EDR', 'Patrimonium', 'Purchase', 'Internal'
    valuation_amount NUMERIC(12,2) NOT NULL,
    valuation_type TEXT, -- 'market_value', 'insurance_value', 'purchase_price'
    appraiser_name TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Indexes
CREATE INDEX idx_valuations_property ON property_valuations(property_id);
CREATE INDEX idx_valuations_date ON property_valuations(valuation_date);
CREATE INDEX idx_valuations_source ON property_valuations(valuation_source);

-- RLS Policies
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public property_valuations are viewable by everyone." ON property_valuations
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own property_valuations." ON property_valuations
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Users can update their own property_valuations." ON property_valuations
    FOR UPDATE USING (auth.uid() IS NOT NULL);

CREATE POLICY "Users can delete their own property_valuations." ON property_valuations
    FOR DELETE USING (auth.uid() IS NOT NULL);

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'property_valuations' 
        AND policyname = 'service_role_all_property_valuations'
    ) THEN
        CREATE POLICY service_role_all_property_valuations ON property_valuations
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Create view for latest valuation per property
CREATE OR REPLACE VIEW vw_latest_property_valuations AS
SELECT DISTINCT ON (pv.property_id)
    pv.property_id,
    p.name as property_name,
    pv.valuation_date,
    pv.valuation_source,
    pv.valuation_amount,
    p.purchase_price,
    p.purchase_date,
    CASE 
        WHEN p.purchase_price > 0 
        THEN ROUND((pv.valuation_amount - p.purchase_price) / p.purchase_price * 100, 2)
        ELSE NULL
    END as appreciation_percentage,
    pv.valuation_amount - p.purchase_price as absolute_gain
FROM property_valuations pv
JOIN properties p ON pv.property_id = p.id
WHERE pv.valuation_type = 'market_value'
ORDER BY pv.property_id, pv.valuation_date DESC;

COMMENT ON TABLE property_valuations IS 'Multiple valuations/appraisals for each property from different sources';
COMMENT ON VIEW vw_latest_property_valuations IS 'Latest market valuation for each property with appreciation vs purchase price';

