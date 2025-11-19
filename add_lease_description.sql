-- Add description column to leases table for parking and other details
ALTER TABLE leases 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add parking_fee column for explicit parking charges
ALTER TABLE leases 
ADD COLUMN IF NOT EXISTS parking_fee NUMERIC(10,2);

-- Add parking_included boolean flag
ALTER TABLE leases 
ADD COLUMN IF NOT EXISTS parking_included BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN leases.description IS 'Description des particularités du bail (parking, annexes, etc.)';
COMMENT ON COLUMN leases.parking_fee IS 'Montant du parking si payé en sus du loyer net';
COMMENT ON COLUMN leases.parking_included IS 'TRUE si place de parc incluse dans loyer net';


