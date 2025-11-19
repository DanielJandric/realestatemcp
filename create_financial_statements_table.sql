-- Create financial statements table for P&L data
CREATE TABLE IF NOT EXISTS financial_statements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Revenue items
    rental_income_apartments NUMERIC(12,2),
    rental_income_offices NUMERIC(12,2),
    rental_income_commercial NUMERIC(12,2),
    rental_income_parking NUMERIC(12,2),
    rental_income_other NUMERIC(12,2),
    rental_income_total NUMERIC(12,2),
    
    -- Vacancy
    vacancy_amount NUMERIC(12,2),
    vacancy_rate NUMERIC(5,2),
    
    -- Operating expenses
    maintenance_costs NUMERIC(12,2),
    utilities_costs NUMERIC(12,2),
    insurance_costs NUMERIC(12,2),
    property_tax NUMERIC(12,2),
    management_fees NUMERIC(12,2),
    other_expenses NUMERIC(12,2),
    total_expenses NUMERIC(12,2),
    
    -- Financial result
    net_operating_income NUMERIC(12,2),
    financial_charges NUMERIC(12,2),
    net_income NUMERIC(12,2),
    
    -- Additional info
    account_code TEXT,
    line_item TEXT,
    description TEXT,
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_financial_property ON financial_statements(property_id);
CREATE INDEX IF NOT EXISTS idx_financial_period ON financial_statements(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_financial_account ON financial_statements(account_code);

-- Comments
COMMENT ON TABLE financial_statements IS 'Comptes de résultat et données financières par propriété';
COMMENT ON COLUMN financial_statements.period_start IS 'Début de la période (ex: 01.01.2023)';
COMMENT ON COLUMN financial_statements.period_end IS 'Fin de la période (ex: 10.12.2024)';
COMMENT ON COLUMN financial_statements.rental_income_total IS 'Revenus locatifs totaux';
COMMENT ON COLUMN financial_statements.vacancy_amount IS 'Montant des loyers perdus (vacance)';
COMMENT ON COLUMN financial_statements.net_operating_income IS 'Résultat d''exploitation net (NOI)';

-- Enable RLS
ALTER TABLE financial_statements ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY service_role_all_financial ON financial_statements
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


