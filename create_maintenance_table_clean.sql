-- Drop existing table if any issues
DROP TABLE IF EXISTS maintenance CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create maintenance contracts table (clean)
CREATE TABLE maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL,
    unit_id UUID,
    vendor_name TEXT NOT NULL,
    contract_type TEXT,
    description TEXT,
    annual_cost NUMERIC(10,2),
    frequency TEXT,
    start_date DATE,
    end_date DATE,
    notice_period TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    
    -- Foreign keys
    CONSTRAINT fk_maintenance_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    CONSTRAINT fk_maintenance_unit FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX idx_maintenance_property ON maintenance(property_id);
CREATE INDEX idx_maintenance_unit ON maintenance(unit_id);
CREATE INDEX idx_maintenance_status ON maintenance(status);
CREATE INDEX idx_maintenance_vendor ON maintenance(vendor_name);

-- Add comments
COMMENT ON TABLE maintenance IS 'Contrats de maintenance et d''entretien';
COMMENT ON COLUMN maintenance.vendor_name IS 'Nom du prestataire';
COMMENT ON COLUMN maintenance.contract_type IS 'Type de contrat (chauffage, ascenseur, conciergerie, etc.)';
COMMENT ON COLUMN maintenance.annual_cost IS 'Coût annuel HT en CHF';
COMMENT ON COLUMN maintenance.frequency IS 'Fréquence d''intervention';
COMMENT ON COLUMN maintenance.status IS 'Statut: active, terminated, to_terminate';

-- Enable RLS
ALTER TABLE maintenance ENABLE ROW LEVEL SECURITY;

-- Create policy for service_role
CREATE POLICY service_role_all_maintenance ON maintenance
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


