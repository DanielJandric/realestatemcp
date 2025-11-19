-- Add unit_type column to units table if it doesn't exist
ALTER TABLE units ADD COLUMN IF NOT EXISTS unit_type TEXT;

-- Add other enrichment columns
ALTER TABLE units ADD COLUMN IF NOT EXISTS rooms NUMERIC;
ALTER TABLE units ADD COLUMN IF NOT EXISTS balcony BOOLEAN DEFAULT FALSE;
ALTER TABLE units ADD COLUMN IF NOT EXISTS condition_rating INTEGER CHECK (condition_rating BETWEEN 1 AND 5);
ALTER TABLE units ADD COLUMN IF NOT EXISTS last_renovation_date DATE;

-- Add tenant enrichment columns
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS company_name TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS nationality TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS emergency_contact TEXT;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS payment_method TEXT CHECK (payment_method IN ('bank_transfer', 'direct_debit', 'other'));
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS iban TEXT;

-- Add lease_id to documents for linking
ALTER TABLE documents ADD COLUMN IF NOT EXISTS lease_id UUID REFERENCES leases(id) ON DELETE SET NULL;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_units_type ON units(unit_type);
CREATE INDEX IF NOT EXISTS idx_documents_lease_id ON documents(lease_id);

-- Add check constraint for unit_type
ALTER TABLE units DROP CONSTRAINT IF EXISTS valid_unit_type;
ALTER TABLE units ADD CONSTRAINT valid_unit_type 
  CHECK (unit_type IN ('appartement', 'bureau', 'commerce', 'parking', 'cave', 'restaurant', 'atelier', NULL));


