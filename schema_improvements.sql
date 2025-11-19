-- ==================== SCHEMA IMPROVEMENTS ====================
-- Complete enhancement package for the property management database
-- Run this after the base schema_enhanced.sql

-- ==================== PART 1: INTEGRITY CONSTRAINTS ====================

-- Prevent multiple active leases on the same unit
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_lease_per_unit 
ON leases(unit_id) 
WHERE status = 'active';

-- Ensure unique unit_number per property
CREATE UNIQUE INDEX IF NOT EXISTS idx_unit_number_per_property 
ON units(property_id, unit_number);

-- Prevent lease date overlaps on same unit
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Drop the constraint if it exists (for re-runs)
ALTER TABLE leases DROP CONSTRAINT IF EXISTS no_lease_overlap;

-- Add constraint to prevent overlapping active leases
ALTER TABLE leases 
ADD CONSTRAINT no_lease_overlap 
EXCLUDE USING gist (
    unit_id WITH =, 
    daterange(start_date, COALESCE(end_date, '9999-12-31'::date), '[]') WITH &&
) WHERE (status = 'active');

-- ==================== PART 2: RENT HISTORY TRACKING ====================

-- Table for tracking rent changes over time
CREATE TABLE IF NOT EXISTS rent_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lease_id UUID REFERENCES leases(id) ON DELETE CASCADE,
    old_rent NUMERIC,
    new_rent NUMERIC,
    change_date DATE NOT NULL,
    change_reason TEXT,
    changed_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT old_rent_non_negative CHECK (old_rent IS NULL OR old_rent >= 0),
    CONSTRAINT new_rent_non_negative CHECK (new_rent IS NULL OR new_rent >= 0)
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_rent_history_lease_id ON rent_history(lease_id);
CREATE INDEX IF NOT EXISTS idx_rent_history_change_date ON rent_history(change_date DESC);

-- Trigger to automatically track rent changes
CREATE OR REPLACE FUNCTION track_rent_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.rent_net IS DISTINCT FROM NEW.rent_net THEN
        INSERT INTO rent_history (lease_id, old_rent, new_rent, change_date)
        VALUES (NEW.id, OLD.rent_net, NEW.rent_net, CURRENT_DATE);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS rent_change_trigger ON leases;
CREATE TRIGGER rent_change_trigger
AFTER UPDATE ON leases
FOR EACH ROW EXECUTE FUNCTION track_rent_changes();

-- ==================== PART 3: ENHANCE EXISTING TABLES ====================

-- Enhance properties table
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS year_built INTEGER CHECK (year_built > 1800 AND year_built <= EXTRACT(YEAR FROM CURRENT_DATE) + 5),
ADD COLUMN IF NOT EXISTS total_surface_area NUMERIC CHECK (total_surface_area IS NULL OR total_surface_area > 0),
ADD COLUMN IF NOT EXISTS cadastral_ref TEXT,
ADD COLUMN IF NOT EXISTS property_manager TEXT,
ADD COLUMN IF NOT EXISTS acquisition_date DATE,
ADD COLUMN IF NOT EXISTS acquisition_price NUMERIC CHECK (acquisition_price IS NULL OR acquisition_price >= 0);

-- Enhance leases table
ALTER TABLE leases 
ADD COLUMN IF NOT EXISTS payment_day INTEGER CHECK (payment_day IS NULL OR (payment_day BETWEEN 1 AND 31)),
ADD COLUMN IF NOT EXISTS indexation_ref TEXT,
ADD COLUMN IF NOT EXISTS indexation_date DATE,
ADD COLUMN IF NOT EXISTS notice_period_months INTEGER DEFAULT 3 CHECK (notice_period_months > 0),
ADD COLUMN IF NOT EXISTS auto_renewal BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS guarantor_name TEXT,
ADD COLUMN IF NOT EXISTS guarantor_phone TEXT;

-- Enhance tenants table
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS company_name TEXT,
ADD COLUMN IF NOT EXISTS date_of_birth DATE CHECK (date_of_birth IS NULL OR date_of_birth < CURRENT_DATE),
ADD COLUMN IF NOT EXISTS nationality TEXT,
ADD COLUMN IF NOT EXISTS emergency_contact TEXT,
ADD COLUMN IF NOT EXISTS emergency_phone TEXT,
ADD COLUMN IF NOT EXISTS payment_method TEXT CHECK (payment_method IS NULL OR payment_method IN ('bank_transfer', 'direct_debit', 'cash', 'check', 'other')),
ADD COLUMN IF NOT EXISTS iban TEXT,
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Enhance units table
ALTER TABLE units 
ADD COLUMN IF NOT EXISTS balcony BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS parking_spaces INTEGER DEFAULT 0 CHECK (parking_spaces >= 0),
ADD COLUMN IF NOT EXISTS storage BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS condition_rating INTEGER CHECK (condition_rating IS NULL OR (condition_rating BETWEEN 1 AND 5)),
ADD COLUMN IF NOT EXISTS last_renovation_date DATE;

-- ==================== PART 4: NEW TABLES ====================

-- Rent payments tracking
CREATE TABLE IF NOT EXISTS rent_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lease_id UUID REFERENCES leases(id) ON DELETE CASCADE NOT NULL,
    payment_date DATE NOT NULL,
    amount NUMERIC NOT NULL CHECK (amount > 0),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    payment_method TEXT CHECK (payment_method IN ('bank_transfer', 'direct_debit', 'cash', 'check', 'other')),
    reference TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'received', 'late', 'cancelled', 'refunded')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT payment_period_logical CHECK (period_end >= period_start)
);

CREATE INDEX IF NOT EXISTS idx_rent_payments_lease_id ON rent_payments(lease_id);
CREATE INDEX IF NOT EXISTS idx_rent_payments_payment_date ON rent_payments(payment_date DESC);
CREATE INDEX IF NOT EXISTS idx_rent_payments_status ON rent_payments(status);

-- Inspections tracking
CREATE TABLE IF NOT EXISTS inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_id UUID REFERENCES units(id) ON DELETE CASCADE NOT NULL,
    lease_id UUID REFERENCES leases(id) ON DELETE SET NULL,
    inspection_date DATE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('move_in', 'move_out', 'periodic', 'emergency', 'maintenance')),
    inspector TEXT,
    report_path TEXT,
    condition_rating INTEGER CHECK (condition_rating IS NULL OR (condition_rating BETWEEN 1 AND 5)),
    notes TEXT,
    photos_path TEXT,
    issues_found TEXT,
    action_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inspections_unit_id ON inspections(unit_id);
CREATE INDEX IF NOT EXISTS idx_inspections_lease_id ON inspections(lease_id);
CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections(inspection_date DESC);
CREATE INDEX IF NOT EXISTS idx_inspections_type ON inspections(type);

-- Charge details (utility settlements)
CREATE TABLE IF NOT EXISTS charge_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lease_id UUID REFERENCES leases(id) ON DELETE CASCADE NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1),
    heating NUMERIC DEFAULT 0 CHECK (heating >= 0),
    water NUMERIC DEFAULT 0 CHECK (water >= 0),
    electricity NUMERIC DEFAULT 0 CHECK (electricity >= 0),
    maintenance NUMERIC DEFAULT 0 CHECK (maintenance >= 0),
    garbage NUMERIC DEFAULT 0 CHECK (garbage >= 0),
    insurance NUMERIC DEFAULT 0 CHECK (insurance >= 0),
    other NUMERIC DEFAULT 0 CHECK (other >= 0),
    total NUMERIC GENERATED ALWAYS AS (
        COALESCE(heating, 0) + COALESCE(water, 0) + 
        COALESCE(electricity, 0) + COALESCE(maintenance, 0) + 
        COALESCE(garbage, 0) + COALESCE(insurance, 0) +
        COALESCE(other, 0)
    ) STORED,
    statement_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Ensure one statement per lease per year
    CONSTRAINT unique_lease_year UNIQUE(lease_id, year)
);

CREATE INDEX IF NOT EXISTS idx_charge_details_lease_id ON charge_details(lease_id);
CREATE INDEX IF NOT EXISTS idx_charge_details_year ON charge_details(year DESC);

-- Lease renewals tracking
CREATE TABLE IF NOT EXISTS lease_renewals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    old_lease_id UUID REFERENCES leases(id) ON DELETE SET NULL,
    new_lease_id UUID REFERENCES leases(id) ON DELETE CASCADE NOT NULL,
    renewal_date DATE NOT NULL,
    rent_change_amount NUMERIC,
    rent_change_percent NUMERIC,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lease_renewals_old_lease ON lease_renewals(old_lease_id);
CREATE INDEX IF NOT EXISTS idx_lease_renewals_new_lease ON lease_renewals(new_lease_id);

-- Communication log
CREATE TABLE IF NOT EXISTS communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    communication_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type TEXT CHECK (type IN ('email', 'phone', 'letter', 'meeting', 'sms', 'other')),
    subject TEXT,
    content TEXT,
    direction TEXT CHECK (direction IN ('inbound', 'outbound')),
    handled_by TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_communications_tenant_id ON communications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_communications_property_id ON communications(property_id);
CREATE INDEX IF NOT EXISTS idx_communications_date ON communications(communication_date DESC);
CREATE INDEX IF NOT EXISTS idx_communications_follow_up ON communications(follow_up_required, follow_up_date) WHERE follow_up_required = TRUE;

-- ==================== PART 5: ADDITIONAL MATERIALIZED VIEWS ====================

-- Tenant turnover analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tenant_turnover AS
SELECT 
    p.id as property_id,
    p.name as property_name,
    p.city,
    COUNT(DISTINCT l.tenant_id) as total_tenants,
    COUNT(DISTINCT CASE WHEN l.end_date IS NOT NULL AND l.end_date < CURRENT_DATE THEN l.tenant_id END) as churned_tenants,
    ROUND(
        COUNT(DISTINCT CASE WHEN l.end_date IS NOT NULL AND l.end_date < CURRENT_DATE THEN l.tenant_id END)::NUMERIC / 
        NULLIF(COUNT(DISTINCT l.tenant_id), 0) * 100, 2
    ) as churn_rate,
    ROUND(AVG(
        CASE 
            WHEN l.end_date IS NOT NULL AND l.start_date IS NOT NULL
            THEN (l.end_date - l.start_date) / 30.0 
            ELSE NULL 
        END
    ), 1) as avg_tenure_months
FROM properties p
LEFT JOIN units u ON u.property_id = p.id
LEFT JOIN leases l ON l.unit_id = u.id
WHERE l.start_date IS NOT NULL
GROUP BY p.id, p.name, p.city;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_tenant_turnover_property ON mv_tenant_turnover(property_id);

-- Maintenance alerts
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maintenance_alerts AS
SELECT 
    p.id as property_id,
    p.name as property_name,
    p.city,
    COUNT(DISTINCT m.id) FILTER (WHERE m.end_date IS NULL) as ongoing_maintenance,
    COALESCE(SUM(m.cost) FILTER (WHERE m.start_date >= CURRENT_DATE - INTERVAL '12 months'), 0) as yearly_maintenance_cost,
    COUNT(DISTINCT i.id) FILTER (WHERE i.status NOT IN ('closed', 'resolved')) as open_incidents,
    COUNT(DISTINCT d.id) FILTER (WHERE d.status IN ('open', 'in_progress')) as active_disputes
FROM properties p
LEFT JOIN maintenance m ON m.property_id = p.id
LEFT JOIN incidents i ON i.property_id = p.id
LEFT JOIN disputes d ON d.property_id = p.id
GROUP BY p.id, p.name, p.city;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_maintenance_alerts_property ON mv_maintenance_alerts(property_id);

-- Payment status overview
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_payment_status AS
SELECT 
    p.id as property_id,
    p.name as property_name,
    COUNT(DISTINCT l.id) as active_leases,
    COUNT(DISTINCT rp.id) FILTER (WHERE rp.status = 'received') as payments_received,
    COUNT(DISTINCT rp.id) FILTER (WHERE rp.status = 'late') as payments_late,
    COUNT(DISTINCT rp.id) FILTER (WHERE rp.status = 'pending') as payments_pending,
    COALESCE(SUM(rp.amount) FILTER (WHERE rp.status = 'received' AND rp.payment_date >= CURRENT_DATE - INTERVAL '12 months'), 0) as yearly_collections,
    COALESCE(SUM(rp.amount) FILTER (WHERE rp.status = 'late'), 0) as outstanding_amount
FROM properties p
LEFT JOIN units u ON u.property_id = p.id
LEFT JOIN leases l ON l.unit_id = u.id AND l.status = 'active'
LEFT JOIN rent_payments rp ON rp.lease_id = l.id
GROUP BY p.id, p.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_payment_status_property ON mv_payment_status(property_id);

-- Unit condition report
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_unit_condition AS
SELECT 
    p.id as property_id,
    p.name as property_name,
    u.id as unit_id,
    u.unit_number,
    u.condition_rating,
    u.last_renovation_date,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.last_renovation_date))::INTEGER as years_since_renovation,
    COUNT(DISTINCT i.id) as inspection_count,
    MAX(i.inspection_date) as last_inspection_date,
    AVG(i.condition_rating) as avg_inspection_rating,
    COUNT(DISTINCT ins.id) FILTER (WHERE ins.status NOT IN ('closed', 'resolved')) as open_incidents
FROM units u
JOIN properties p ON p.id = u.property_id
LEFT JOIN inspections i ON i.unit_id = u.id
LEFT JOIN incidents ins ON ins.property_id = p.id
GROUP BY p.id, p.name, u.id, u.unit_number, u.condition_rating, u.last_renovation_date;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_unit_condition_unit ON mv_unit_condition(unit_id);

-- ==================== PART 6: UTILITY FUNCTIONS ====================

-- Get current vacancy rate
CREATE OR REPLACE FUNCTION get_vacancy_rate(p_property_id UUID)
RETURNS NUMERIC
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(ROUND(
        (1 - COUNT(DISTINCT l.id)::NUMERIC / NULLIF(COUNT(DISTINCT u.id), 0)) * 100, 2
    ), 0)
    FROM units u
    LEFT JOIN leases l ON l.unit_id = u.id AND l.status = 'active'
    WHERE u.property_id = p_property_id;
$$;

-- Project annual revenue
CREATE OR REPLACE FUNCTION project_annual_revenue(p_property_id UUID)
RETURNS NUMERIC
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(SUM((l.rent_net + COALESCE(l.charges, 0)) * 12), 0)
    FROM leases l
    JOIN units u ON u.id = l.unit_id
    WHERE u.property_id = p_property_id AND l.status = 'active';
$$;

-- Get expiring leases
CREATE OR REPLACE FUNCTION get_expiring_leases(months_ahead INTEGER DEFAULT 3)
RETURNS TABLE(
    lease_id UUID,
    tenant_name TEXT,
    property_name TEXT,
    unit_number TEXT,
    end_date DATE,
    days_until_expiry INTEGER,
    monthly_rent NUMERIC
)
LANGUAGE SQL
STABLE
AS $$
    SELECT 
        l.id,
        t.name,
        p.name,
        u.unit_number,
        l.end_date,
        (l.end_date - CURRENT_DATE)::INTEGER,
        l.rent_net
    FROM leases l
    JOIN tenants t ON t.id = l.tenant_id
    JOIN units u ON u.id = l.unit_id
    JOIN properties p ON p.id = u.property_id
    WHERE l.status = 'active'
        AND l.end_date IS NOT NULL
        AND l.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + (months_ahead || ' months')::INTERVAL
    ORDER BY l.end_date;
$$;

-- Calculate average rent per sqm for a property
CREATE OR REPLACE FUNCTION get_avg_rent_per_sqm(p_property_id UUID)
RETURNS NUMERIC
LANGUAGE SQL
STABLE
AS $$
    SELECT ROUND(AVG(l.rent_net / NULLIF(u.surface_area, 0)), 2)
    FROM leases l
    JOIN units u ON u.id = l.unit_id
    WHERE u.property_id = p_property_id 
        AND l.status = 'active'
        AND u.surface_area > 0;
$$;

-- Get late payments for a property
CREATE OR REPLACE FUNCTION get_late_payments(p_property_id UUID, days_overdue INTEGER DEFAULT 0)
RETURNS TABLE(
    payment_id UUID,
    tenant_name TEXT,
    unit_number TEXT,
    amount NUMERIC,
    payment_date DATE,
    days_late INTEGER
)
LANGUAGE SQL
STABLE
AS $$
    SELECT 
        rp.id,
        t.name,
        u.unit_number,
        rp.amount,
        rp.payment_date,
        (CURRENT_DATE - rp.payment_date)::INTEGER
    FROM rent_payments rp
    JOIN leases l ON l.id = rp.lease_id
    JOIN tenants t ON t.id = l.tenant_id
    JOIN units u ON u.id = l.unit_id
    WHERE u.property_id = p_property_id
        AND rp.status IN ('pending', 'late')
        AND rp.payment_date < CURRENT_DATE - (days_overdue || ' days')::INTERVAL
    ORDER BY rp.payment_date;
$$;

-- Calculate collection rate
CREATE OR REPLACE FUNCTION get_collection_rate(p_property_id UUID, p_year INTEGER DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER)
RETURNS NUMERIC
LANGUAGE SQL
STABLE
AS $$
    WITH expected AS (
        SELECT SUM((l.rent_net + COALESCE(l.charges, 0)) * 12) as expected_annual
        FROM leases l
        JOIN units u ON u.id = l.unit_id
        WHERE u.property_id = p_property_id
            AND l.status = 'active'
            AND EXTRACT(YEAR FROM l.start_date) <= p_year
    ),
    collected AS (
        SELECT SUM(rp.amount) as collected_amount
        FROM rent_payments rp
        JOIN leases l ON l.id = rp.lease_id
        JOIN units u ON u.id = l.unit_id
        WHERE u.property_id = p_property_id
            AND rp.status = 'received'
            AND EXTRACT(YEAR FROM rp.payment_date) = p_year
    )
    SELECT ROUND(
        COALESCE(c.collected_amount / NULLIF(e.expected_annual, 0) * 100, 0), 2
    )
    FROM expected e, collected c;
$$;

-- Get tenant payment history
CREATE OR REPLACE FUNCTION get_tenant_payment_history(p_tenant_id UUID)
RETURNS TABLE(
    payment_date DATE,
    amount NUMERIC,
    status TEXT,
    property_name TEXT,
    unit_number TEXT
)
LANGUAGE SQL
STABLE
AS $$
    SELECT 
        rp.payment_date,
        rp.amount,
        rp.status,
        p.name,
        u.unit_number
    FROM rent_payments rp
    JOIN leases l ON l.id = rp.lease_id
    JOIN units u ON u.id = l.unit_id
    JOIN properties p ON p.id = u.property_id
    WHERE l.tenant_id = p_tenant_id
    ORDER BY rp.payment_date DESC;
$$;

-- Update materialized views function
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_portfolio_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_property_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_unit_type_analysis;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tenant_turnover;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_maintenance_alerts;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_payment_status;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_unit_condition;
END;
$$;

-- ==================== PART 7: ROW-LEVEL SECURITY ====================

-- Enable RLS on all tables
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE units ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE leases ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE rent_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE charge_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE communications ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS service_role_all_properties ON properties;
DROP POLICY IF EXISTS service_role_all_units ON units;
DROP POLICY IF EXISTS service_role_all_tenants ON tenants;
DROP POLICY IF EXISTS service_role_all_leases ON leases;
DROP POLICY IF EXISTS authenticated_read_properties ON properties;
DROP POLICY IF EXISTS authenticated_read_units ON units;
DROP POLICY IF EXISTS authenticated_read_leases ON leases;

-- Create policies for service role (bypass RLS for service_role key)
CREATE POLICY service_role_all_properties ON properties
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_units ON units
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_tenants ON tenants
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_leases ON leases
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_documents ON documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_disputes ON disputes
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_incidents ON incidents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_maintenance ON maintenance
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_rent_payments ON rent_payments
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_inspections ON inspections
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_charge_details ON charge_details
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY service_role_all_communications ON communications
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Allow read access for authenticated users
CREATE POLICY authenticated_read_properties ON properties
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY authenticated_read_units ON units
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY authenticated_read_leases ON leases
    FOR SELECT
    TO authenticated
    USING (true);

-- Note: For production, implement proper role-based access control
-- Example: USING (property_manager = auth.uid()::text) for property-manager-specific access

-- ==================== INDEXES FOR AUDIT ====================
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);

-- ==================== COMMENTS (DOCUMENTATION) ====================

COMMENT ON TABLE rent_history IS 'Tracks all changes to rent amounts over time';
COMMENT ON TABLE rent_payments IS 'Records individual rent payment transactions';
COMMENT ON TABLE inspections IS 'Unit inspection reports and condition assessments';
COMMENT ON TABLE charge_details IS 'Annual utility charge settlements';
COMMENT ON TABLE lease_renewals IS 'Links old and new leases when contracts are renewed';
COMMENT ON TABLE communications IS 'Log of all communications with tenants';

COMMENT ON FUNCTION get_vacancy_rate IS 'Calculate current vacancy rate as percentage for a property';
COMMENT ON FUNCTION project_annual_revenue IS 'Project annual revenue based on current active leases';
COMMENT ON FUNCTION get_expiring_leases IS 'Get list of leases expiring within specified months';
COMMENT ON FUNCTION get_collection_rate IS 'Calculate rent collection rate as percentage for a property';

-- ==================== COMPLETION ====================

DO $$
BEGIN
    RAISE NOTICE 'Schema improvements applied successfully!';
    RAISE NOTICE 'Added: Integrity constraints, rent history, new tables, materialized views, utility functions, and RLS';
    RAISE NOTICE 'Run: SELECT refresh_all_materialized_views(); to populate views';
END $$;

