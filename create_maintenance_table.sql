-- Create maintenance contracts table
CREATE TABLE IF NOT EXISTS maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    unit_id UUID REFERENCES units(id) ON DELETE SET NULL,  -- References units.id
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_maintenance_property ON maintenance(property_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_unit ON maintenance(unit_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance(status);
CREATE INDEX IF NOT EXISTS idx_maintenance_vendor ON maintenance(vendor_name);

-- Add comments
COMMENT ON TABLE maintenance IS 'Contrats de maintenance et d''entretien';
COMMENT ON COLUMN maintenance.vendor_name IS 'Nom du prestataire';
COMMENT ON COLUMN maintenance.contract_type IS 'Type de contrat (chauffage, ascenseur, conciergerie, etc.)';
COMMENT ON COLUMN maintenance.annual_cost IS 'Coût annuel HT en CHF';
COMMENT ON COLUMN maintenance.frequency IS 'Fréquence d''intervention';
COMMENT ON COLUMN maintenance.status IS 'Statut: active, terminated, to_terminate';

-- RLS policies
ALTER TABLE maintenance ENABLE ROW LEVEL SECURITY;

CREATE POLICY service_role_all_maintenance ON maintenance
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

