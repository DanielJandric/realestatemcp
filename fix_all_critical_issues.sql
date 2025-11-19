-- ═══════════════════════════════════════════════════════════════
-- CORRECTIONS CRITIQUES DU SYSTÈME MCP IMMOBILIER
-- Basé sur l'analyse de Claude
-- ═══════════════════════════════════════════════════════════════

-- 1. NORMALISER LES STATUTS DES BAUX
UPDATE leases 
SET status = 'Actif' 
WHERE LOWER(status) IN ('active', 'actif');

UPDATE leases 
SET status = 'Terminé' 
WHERE LOWER(status) IN ('terminated', 'terminé', 'expired');

UPDATE leases 
SET status = 'En cours' 
WHERE status IS NULL AND (end_date IS NULL OR end_date > NOW());

-- 2. STANDARDISER LES TYPES D'UNITÉS (Capitaliser)
UPDATE units 
SET type = CASE 
    WHEN LOWER(type) LIKE '%appartement%' THEN 'Appartement'
    WHEN LOWER(type) LIKE '%magasin%' OR LOWER(type) LIKE '%commerce%' THEN 'Magasin'
    WHEN LOWER(type) LIKE '%bureau%' OR LOWER(type) LIKE '%büro%' THEN 'Bureau'
    WHEN LOWER(type) LIKE '%parking%' OR LOWER(type) LIKE '%place%' OR LOWER(type) LIKE '%garage%' THEN 'Parking'
    WHEN LOWER(type) LIKE '%dépôt%' OR LOWER(type) LIKE '%depot%' OR LOWER(type) LIKE '%cave%' THEN 'Dépôt'
    WHEN LOWER(type) LIKE '%local%' THEN 'Local technique'
    ELSE INITCAP(type)
END;

-- 3. AJOUTER COLONNE is_active SI MANQUANTE (pour servitudes)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'servitudes' AND column_name = 'is_active') THEN
        ALTER TABLE servitudes ADD COLUMN is_active BOOLEAN DEFAULT true;
        UPDATE servitudes SET is_active = true;
    END IF;
END $$;

-- 4. CRÉER VUE CONSOLIDÉE POUR REVENUS
CREATE OR REPLACE VIEW v_revenue_summary AS
SELECT 
    p.id as property_id,
    p.name as property_name,
    COUNT(DISTINCT u.id) as total_units,
    COUNT(DISTINCT CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN l.id END) as occupied_units,
    SUM(CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN l.rent_net ELSE 0 END) as monthly_rent,
    SUM(CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN l.charges ELSE 0 END) as monthly_charges,
    SUM(CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN (l.rent_net + l.charges) ELSE 0 END) as monthly_revenue,
    SUM(CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN (l.rent_net + l.charges) * 12 ELSE 0 END) as annual_revenue,
    ROUND(
        COUNT(DISTINCT CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN l.id END)::numeric / 
        NULLIF(COUNT(DISTINCT u.id), 0) * 100, 
        2
    ) as occupation_rate
FROM properties p
LEFT JOIN units u ON u.property_id = p.id
LEFT JOIN leases l ON l.unit_id = u.id
GROUP BY p.id, p.name;

-- 5. CRÉER VUE POUR BAUX EXPIRANTS
CREATE OR REPLACE VIEW v_expiring_leases AS
SELECT 
    l.*,
    p.name as property_name,
    u.unit_number,
    t.name as tenant_name,
    EXTRACT(DAYS FROM l.end_date - NOW()) as days_until_expiry,
    CASE 
        WHEN l.end_date < NOW() THEN 'Expiré'
        WHEN l.end_date < NOW() + INTERVAL '3 months' THEN 'Urgent'
        WHEN l.end_date < NOW() + INTERVAL '6 months' THEN 'À surveiller'
        ELSE 'Normal'
    END as urgency
FROM leases l
JOIN units u ON l.unit_id = u.id
JOIN properties p ON u.property_id = p.id
LEFT JOIN tenants t ON l.tenant_id = t.id
WHERE l.end_date IS NOT NULL 
  AND l.end_date < NOW() + INTERVAL '12 months'
ORDER BY l.end_date;

-- 6. CRÉER VUE POUR ANOMALIES LOYERS
CREATE OR REPLACE VIEW v_rent_anomalies AS
WITH rent_stats AS (
    SELECT 
        u.type,
        AVG(l.rent_net) as avg_rent,
        STDDEV(l.rent_net) as stddev_rent
    FROM units u
    JOIN leases l ON l.unit_id = u.id
    WHERE l.end_date IS NULL OR l.end_date > NOW()
    GROUP BY u.type
)
SELECT 
    l.id as lease_id,
    p.name as property_name,
    u.unit_number,
    u.type as unit_type,
    l.rent_net,
    rs.avg_rent,
    ROUND((l.rent_net - rs.avg_rent) / NULLIF(rs.stddev_rent, 0), 2) as z_score,
    CASE 
        WHEN ABS((l.rent_net - rs.avg_rent) / NULLIF(rs.stddev_rent, 0)) > 2 THEN 'ANOMALIE'
        WHEN ABS((l.rent_net - rs.avg_rent) / NULLIF(rs.stddev_rent, 0)) > 1.5 THEN 'Suspect'
        ELSE 'Normal'
    END as status
FROM leases l
JOIN units u ON l.unit_id = u.id
JOIN properties p ON u.property_id = p.id
JOIN rent_stats rs ON rs.type = u.type
WHERE l.end_date IS NULL OR l.end_date > NOW()
ORDER BY ABS((l.rent_net - rs.avg_rent) / NULLIF(rs.stddev_rent, 0)) DESC;

-- 7. CRÉER INDEX POUR PERFORMANCE
-- Index sans prédicat NOW() (qui n'est pas IMMUTABLE)
CREATE INDEX IF NOT EXISTS idx_leases_unit ON leases(unit_id);
CREATE INDEX IF NOT EXISTS idx_leases_end_date ON leases(end_date);

CREATE INDEX IF NOT EXISTS idx_units_property ON units(property_id);

CREATE INDEX IF NOT EXISTS idx_units_type ON units(type);

-- 8. GRANT PERMISSIONS SUR VUES
GRANT SELECT ON v_revenue_summary TO authenticated, anon, service_role;
GRANT SELECT ON v_expiring_leases TO authenticated, anon, service_role;
GRANT SELECT ON v_rent_anomalies TO authenticated, anon, service_role;

-- ═══════════════════════════════════════════════════════════════
-- ✅ SCRIPT TERMINÉ
-- ═══════════════════════════════════════════════════════════════
-- PROCHAINES ÉTAPES:
-- 1. Exécuter ce script dans Supabase SQL Editor
-- 2. Redémarrer Claude Desktop
-- 3. Tester: "Donne-moi l'état locatif complet"
-- ═══════════════════════════════════════════════════════════════

