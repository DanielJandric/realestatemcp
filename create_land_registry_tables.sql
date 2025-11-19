-- ============================================================================
-- TABLES REGISTRE FONCIER & SERVITUDES
-- Pour stocker les extraits du registre foncier et les servitudes/restrictions
-- ============================================================================

-- 1. Table pour les servitudes et restrictions
CREATE TABLE IF NOT EXISTS servitudes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    
    -- Identification
    type_servitude TEXT NOT NULL, -- 'servitude', 'restriction', 'charge', 'annotation'
    categorie TEXT, -- 'passage', 'construction', 'usage', 'easement', etc.
    numero_rf TEXT, -- Numéro dans le registre foncier
    
    -- Description
    titre TEXT,
    description TEXT,
    beneficiaire TEXT, -- Qui bénéficie de la servitude
    grevé TEXT, -- Fond grevé (qui supporte la charge)
    
    -- Détails juridiques
    nature_juridique TEXT, -- 'réelle', 'personnelle', 'légale', 'conventionnelle'
    objet TEXT, -- Description de l'objet de la servitude
    etendue TEXT, -- Étendue géographique ou temporelle
    
    -- Surface et localisation
    surface_concernee NUMERIC(10,2), -- m² concernés
    parcelle_numero TEXT,
    plan_reference TEXT,
    
    -- Dates importantes
    date_inscription DATE,
    date_radiation DATE, -- Si annulée
    date_modification DATE,
    
    -- Valeurs
    montant NUMERIC(12,2), -- Si valeur monétaire
    devise TEXT DEFAULT 'CHF',
    indemnite_annuelle NUMERIC(10,2), -- Si indemnité récurrente
    
    -- Conditions
    conditions_execution TEXT,
    duree TEXT, -- 'permanente', 'temporaire', ou durée spécifique
    resiliable BOOLEAN,
    conditions_resiliation TEXT,
    
    -- Impact sur la propriété
    impact_constructibilite BOOLEAN DEFAULT FALSE,
    impact_usage BOOLEAN DEFAULT FALSE,
    impact_valeur BOOLEAN DEFAULT FALSE,
    impact_description TEXT,
    
    -- Parties concernées
    parties_prenantes JSONB, -- Liste des parties impliquées
    contacts JSONB, -- Contacts associés
    
    -- Documents
    document_source_id UUID REFERENCES documents(id),
    numero_page INTEGER, -- Page dans le document source
    extrait_texte TEXT, -- Extrait pertinent du texte
    
    -- Statut et validation
    statut TEXT DEFAULT 'active', -- 'active', 'radiée', 'modifiée', 'en_cours'
    verifie_par TEXT,
    date_verification DATE,
    commentaires TEXT,
    
    -- Importance et alertes
    importance_niveau TEXT, -- 'critique', 'importante', 'normale', 'mineure'
    alerte_expiration BOOLEAN DEFAULT FALSE,
    notes_internes TEXT,
    
    -- Métadonnées
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Table pour les documents du registre foncier
CREATE TABLE IF NOT EXISTS land_registry_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id),
    
    -- Type de document
    document_type TEXT NOT NULL, -- 'extrait_rf', 'plan_affectation', 'reglement_construction', 'restrictions', 'cadastre'
    
    -- Identification RF
    commune TEXT,
    numero_parcelle TEXT,
    numero_bien_fonds TEXT,
    folio TEXT,
    
    -- Informations cadastrales
    surface_totale NUMERIC(10,2), -- m²
    zone_affectation TEXT, -- 'zone_habitation', 'zone_mixte', 'zone_industrielle', etc.
    indice_utilisation_sol NUMERIC(5,2), -- IUS
    taux_occupation_sol NUMERIC(5,2), -- TOS
    hauteur_max_batiment NUMERIC(5,2), -- mètres
    
    -- Propriété
    proprietaire_inscrit TEXT,
    forme_propriete TEXT, -- 'propriété_exclusive', 'copropriété', 'propriété_par_étages'
    quote_part TEXT, -- Si copropriété
    
    -- Charges et servitudes (résumé)
    a_servitudes BOOLEAN DEFAULT FALSE,
    nombre_servitudes INTEGER DEFAULT 0,
    a_restrictions BOOLEAN DEFAULT FALSE,
    nombre_restrictions INTEGER DEFAULT 0,
    a_charges BOOLEAN DEFAULT FALSE,
    a_gages BOOLEAN DEFAULT FALSE,
    
    -- Valeur officielle
    valeur_fiscale NUMERIC(12,2),
    valeur_assurance NUMERIC(12,2),
    annee_valeur INTEGER,
    
    -- Dates du document
    date_extrait DATE, -- Date de l'extrait
    date_etat_parcelle DATE, -- État de la parcelle au...
    annee_construction INTEGER,
    annee_renovation INTEGER,
    
    -- Historique
    historique_modifications JSONB, -- Liste des modifications historiques
    documents_anterieurs TEXT[], -- Références aux extraits précédents
    
    -- Urbanisme
    plan_affectation_zone TEXT,
    reglement_applicable TEXT,
    permis_construire TEXT[],
    
    -- Résumé automatique
    resume_servitudes TEXT, -- Résumé généré des servitudes
    resume_restrictions TEXT, -- Résumé généré des restrictions
    points_attention TEXT[], -- Points d'attention identifiés
    
    -- Validation
    verifie BOOLEAN DEFAULT FALSE,
    verifie_par TEXT,
    date_verification DATE,
    
    -- Métadonnées
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Table de liaison servitudes ↔ unités (une servitude peut concerner plusieurs unités)
CREATE TABLE IF NOT EXISTS servitudes_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    servitude_id UUID REFERENCES servitudes(id) ON DELETE CASCADE,
    unit_id UUID REFERENCES units(id) ON DELETE CASCADE,
    impact_direct BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_servitudes_property ON servitudes(property_id);
CREATE INDEX IF NOT EXISTS idx_servitudes_type ON servitudes(type_servitude);
CREATE INDEX IF NOT EXISTS idx_servitudes_statut ON servitudes(statut);
CREATE INDEX IF NOT EXISTS idx_servitudes_importance ON servitudes(importance_niveau);
CREATE INDEX IF NOT EXISTS idx_servitudes_date_inscription ON servitudes(date_inscription);

CREATE INDEX IF NOT EXISTS idx_lrd_property ON land_registry_documents(property_id);
CREATE INDEX IF NOT EXISTS idx_lrd_type ON land_registry_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_lrd_parcelle ON land_registry_documents(numero_parcelle);
CREATE INDEX IF NOT EXISTS idx_lrd_servitudes ON land_registry_documents(a_servitudes) WHERE a_servitudes = true;

CREATE INDEX IF NOT EXISTS idx_servitudes_units_servitude ON servitudes_units(servitude_id);
CREATE INDEX IF NOT EXISTS idx_servitudes_units_unit ON servitudes_units(unit_id);

-- RLS (Row Level Security)
ALTER TABLE servitudes ENABLE ROW LEVEL SECURITY;
ALTER TABLE land_registry_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE servitudes_units ENABLE ROW LEVEL SECURITY;

-- Policies
DO $$ 
BEGIN
    -- Servitudes
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'servitudes' 
        AND policyname = 'service_role_all_servitudes'
    ) THEN
        CREATE POLICY service_role_all_servitudes ON servitudes
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Land registry documents
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'land_registry_documents' 
        AND policyname = 'service_role_all_lrd'
    ) THEN
        CREATE POLICY service_role_all_lrd ON land_registry_documents
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Servitudes units
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'servitudes_units' 
        AND policyname = 'service_role_all_su'
    ) THEN
        CREATE POLICY service_role_all_su ON servitudes_units
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- Vue pour analyse rapide des servitudes par propriété
CREATE OR REPLACE VIEW vw_servitudes_summary AS
SELECT 
    p.name as property_name,
    COUNT(DISTINCT s.id) as total_servitudes,
    COUNT(DISTINCT CASE WHEN s.statut = 'active' THEN s.id END) as servitudes_actives,
    COUNT(DISTINCT CASE WHEN s.type_servitude = 'servitude' THEN s.id END) as servitudes,
    COUNT(DISTINCT CASE WHEN s.type_servitude = 'restriction' THEN s.id END) as restrictions,
    COUNT(DISTINCT CASE WHEN s.type_servitude = 'charge' THEN s.id END) as charges,
    COUNT(DISTINCT CASE WHEN s.importance_niveau = 'critique' THEN s.id END) as critiques,
    COUNT(DISTINCT CASE WHEN s.impact_constructibilite THEN s.id END) as impact_construction,
    COUNT(DISTINCT CASE WHEN s.impact_usage THEN s.id END) as impact_usage,
    SUM(s.indemnite_annuelle) as total_indemnites_annuelles
FROM properties p
LEFT JOIN servitudes s ON s.property_id = p.id
GROUP BY p.id, p.name
ORDER BY total_servitudes DESC;

-- Commentaires
COMMENT ON TABLE servitudes IS 'Servitudes, restrictions et charges grevant les propriétés';
COMMENT ON TABLE land_registry_documents IS 'Documents officiels du registre foncier et cadastre';
COMMENT ON TABLE servitudes_units IS 'Liaison entre servitudes et unités concernées';
COMMENT ON VIEW vw_servitudes_summary IS 'Résumé des servitudes par propriété';

COMMENT ON COLUMN servitudes.type_servitude IS 'Type: servitude, restriction, charge, annotation';
COMMENT ON COLUMN servitudes.importance_niveau IS 'Niveau: critique, importante, normale, mineure';
COMMENT ON COLUMN servitudes.impact_constructibilite IS 'Si TRUE, impacte les droits à bâtir';
COMMENT ON COLUMN land_registry_documents.indice_utilisation_sol IS 'IUS - Indice d''utilisation du sol';
COMMENT ON COLUMN land_registry_documents.taux_occupation_sol IS 'TOS - Taux d''occupation du sol';

