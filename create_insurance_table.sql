-- Create insurance policies table
CREATE TABLE IF NOT EXISTS insurance_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    
    -- Policy identification
    policy_number TEXT,
    policy_type TEXT NOT NULL,  -- 'property', 'liability', 'fire', 'water_damage', 'natural_disasters', etc.
    insurer_name TEXT NOT NULL,
    broker_name TEXT,
    
    -- Coverage details
    coverage_type TEXT,  -- 'all_risk', 'named_perils', 'specific', etc.
    insured_value NUMERIC(15,2),  -- Valeur assurée
    sum_insured NUMERIC(15,2),  -- Somme assurée
    building_value NUMERIC(15,2),  -- Valeur bâtiment
    contents_value NUMERIC(15,2),  -- Valeur contenu
    rental_loss_coverage NUMERIC(15,2),  -- Perte de loyer
    
    -- Premium information
    annual_premium NUMERIC(12,2) NOT NULL,
    premium_frequency TEXT,  -- 'annual', 'semi-annual', 'quarterly', 'monthly'
    payment_method TEXT,
    
    -- Policy dates
    policy_start_date DATE NOT NULL,
    policy_end_date DATE NOT NULL,
    cancellation_notice_days INTEGER,  -- Préavis de résiliation
    
    -- Deductibles
    deductible_amount NUMERIC(12,2),
    deductible_percentage NUMERIC(5,2),
    
    -- Additional coverage
    loss_of_rent_covered BOOLEAN DEFAULT false,
    natural_disasters_covered BOOLEAN DEFAULT false,
    terrorism_covered BOOLEAN DEFAULT false,
    cyber_risk_covered BOOLEAN DEFAULT false,
    
    -- Status
    status TEXT DEFAULT 'active',  -- 'active', 'expired', 'cancelled', 'pending'
    
    -- Additional info
    description TEXT,
    coverage_details TEXT,
    exclusions TEXT,
    special_conditions TEXT,
    notes TEXT,
    document_path TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_insurance_property ON insurance_policies(property_id);
CREATE INDEX IF NOT EXISTS idx_insurance_type ON insurance_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_insurance_insurer ON insurance_policies(insurer_name);
CREATE INDEX IF NOT EXISTS idx_insurance_status ON insurance_policies(status);
CREATE INDEX IF NOT EXISTS idx_insurance_dates ON insurance_policies(policy_start_date, policy_end_date);
CREATE INDEX IF NOT EXISTS idx_insurance_value ON insurance_policies(insured_value);

-- Add comments
COMMENT ON TABLE insurance_policies IS 'Polices d''assurance par propriété';
COMMENT ON COLUMN insurance_policies.policy_type IS 'Type: property, liability, fire, water_damage, etc.';
COMMENT ON COLUMN insurance_policies.insured_value IS 'Valeur totale assurée en CHF';
COMMENT ON COLUMN insurance_policies.annual_premium IS 'Prime annuelle en CHF';
COMMENT ON COLUMN insurance_policies.policy_start_date IS 'Date début police';
COMMENT ON COLUMN insurance_policies.policy_end_date IS 'Date fin/renouvellement police';
COMMENT ON COLUMN insurance_policies.cancellation_notice_days IS 'Préavis de résiliation en jours';

-- Enable RLS
ALTER TABLE insurance_policies ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY service_role_all_insurance ON insurance_policies
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


