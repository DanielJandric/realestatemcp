"""
Correction de l'outil get_etat_locatif_complet
==============================================

Ce fichier contient le code corrigé pour calculer correctement la vacance financière.
À intégrer dans: mcp_server/tools/get_etat_locatif_complet.py
"""

# ============================================================================
# VERSION CORRIGÉE - À copier dans votre outil
# ============================================================================

async def get_etat_locatif_complet(property_name: str | None = None):
    """
    État locatif complet avec calcul CORRECT de la vacance financière.
    
    RÈGLES MÉTIER:
    - Vacant = tenant.name = 'Vacant' (PAS rent_net = 0)
    - Loyer sur Vacant = loyer théorique de marché
    - Vacance financière = perte / revenus_potentiels
    """
    
    # Requête SQL corrigée
    query = """
        SELECT 
            p.id as property_id,
            p.name as property_name,
            u.id as unit_id,
            u.unit_number,
            u.type as unit_type,
            u.surface_area,
            l.rent_net,
            l.charges,
            t.id as tenant_id,
            t.name as tenant_name,
            l.status as lease_status
        FROM properties p
        JOIN units u ON u.property_id = p.id
        JOIN leases l ON l.unit_id = u.id
        LEFT JOIN tenants t ON l.tenant_id = t.id
        WHERE l.status = 'Actif'
    """
    
    if property_name:
        query += " AND p.name ILIKE %(property_name)s"
        params = {"property_name": f"%{property_name}%"}
    else:
        params = None
    
    results = await db.fetch_all(query, params)
    
    if not results:
        return {"error": "Aucune propriété trouvée"}
    
    # Convertir en DataFrame pour calculs
    df = pd.DataFrame([dict(row) for row in results])
    
    # ============================================================================
    # CALCULS CORRECTS
    # ============================================================================
    
    # 1. Identifier les unités par statut
    df['is_vacant'] = df['tenant_name'] == 'Vacant'
    df['is_occupied_paying'] = (df['tenant_name'] != 'Vacant') & (df['rent_net'] > 0)
    df['is_internal_use'] = (df['tenant_name'] != 'Vacant') & (df['rent_net'] == 0)
    
    # 2. Calculer les métriques par propriété
    properties_summary = []
    
    for prop_name, prop_group in df.groupby('property_name'):
        
        total_units = len(prop_group)
        
        # Unités réellement occupées et payantes
        occupied_units = prop_group['is_occupied_paying'].sum()
        
        # Unités vacantes (avec loyer théorique)
        vacant_units = prop_group['is_vacant'].sum()
        
        # Unités usage interne (rent=0)
        internal_use_units = prop_group['is_internal_use'].sum()
        
        # Revenus réels (seulement unités occupées payantes)
        actual_revenue = prop_group[prop_group['is_occupied_paying']]['rent_net'].sum()
        
        # Revenus potentiels (tous les loyers, incluant théoriques sur Vacant)
        potential_revenue = prop_group['rent_net'].sum()
        
        # Perte de vacance (loyers théoriques des unités Vacant)
        vacancy_loss = prop_group[prop_group['is_vacant']]['rent_net'].sum()
        
        # Vacance financière (perte / potentiel)
        if potential_revenue > 0:
            financial_vacancy_pct = (vacancy_loss / potential_revenue) * 100
        else:
            financial_vacancy_pct = 0
        
        # Taux occupation physique (unités non-Vacant / total)
        physical_occupancy = (occupied_units + internal_use_units) / total_units * 100
        
        properties_summary.append({
            "property_id": prop_group.iloc[0]['property_id'],
            "property_name": prop_name,
            "total_units": int(total_units),
            "occupied_units": int(occupied_units),
            "vacant_units": int(vacant_units),
            "internal_use_units": int(internal_use_units),
            "actual_revenue": round(float(actual_revenue), 2),
            "potential_revenue": round(float(potential_revenue), 2),
            "vacancy_loss": round(float(vacancy_loss), 2),
            "financial_vacancy_pct": round(float(financial_vacancy_pct), 2),
            "physical_occupancy_pct": round(float(physical_occupancy), 2),
            "monthly_charges": round(float(prop_group['charges'].sum()), 2),
            "annual_revenue": round(float(potential_revenue * 12), 2),
            "annual_vacancy_loss": round(float(vacancy_loss * 12), 2)
        })
    
    # 3. Calculer totaux portfolio
    portfolio_totals = {
        "total_units": int(df.shape[0]),
        "occupied_units": int(df['is_occupied_paying'].sum()),
        "vacant_units": int(df['is_vacant'].sum()),
        "internal_use_units": int(df['is_internal_use'].sum()),
        "actual_revenue": round(float(df[df['is_occupied_paying']]['rent_net'].sum()), 2),
        "potential_revenue": round(float(df['rent_net'].sum()), 2),
        "vacancy_loss": round(float(df[df['is_vacant']]['rent_net'].sum()), 2),
        "financial_vacancy_pct": round(
            float(df[df['is_vacant']]['rent_net'].sum() / df['rent_net'].sum() * 100)
            if df['rent_net'].sum() > 0 else 0, 2
        ),
        "physical_occupancy_pct": round(
            float((df['is_occupied_paying'].sum() + df['is_internal_use'].sum()) / 
                  df.shape[0] * 100), 2
        ),
        "annual_revenue": round(float(df['rent_net'].sum() * 12), 2),
        "annual_vacancy_loss": round(float(df[df['is_vacant']]['rent_net'].sum() * 12), 2)
    }
    
    return {
        "success": True,
        "properties_count": len(properties_summary),
        "etat_locatif": properties_summary,
        "portfolio_totals": portfolio_totals,
        "calculation_method": "financial_vacancy",
        "calculation_notes": {
            "vacant_definition": "tenant.name = 'Vacant'",
            "vacancy_loss": "Theoretical rent on vacant units",
            "financial_vacancy": "vacancy_loss / potential_revenue * 100",
            "internal_use": "Units with rent=0 but not vacant (parking inclus, etc.)"
        }
    }


# ============================================================================
# FONCTION DE VALIDATION (optionnelle mais recommandée)
# ============================================================================

async def validate_vacancy_data():
    """
    Valide que les données respectent les règles métier.
    À appeler périodiquement ou avant les rapports.
    """
    
    validations = []
    
    # Test 1: Aucune unité Vacant ne devrait avoir rent=0
    query1 = """
        SELECT COUNT(*) as count
        FROM leases l
        JOIN tenants t ON l.tenant_id = t.id
        WHERE l.status = 'Actif' 
          AND t.name = 'Vacant' 
          AND l.rent_net = 0
    """
    result1 = await db.fetch_one(query1)
    
    validations.append({
        "test": "Unités Vacant avec loyer théorique = 0",
        "result": result1['count'],
        "expected": 0,
        "status": "✅ PASS" if result1['count'] == 0 else "❌ FAIL",
        "action": "Définir loyer théorique de marché" if result1['count'] > 0 else None
    })
    
    # Test 2: Cohérence des totaux
    query2 = """
        SELECT 
            SUM(CASE WHEN t.name != 'Vacant' AND l.rent_net > 0 
                THEN l.rent_net ELSE 0 END) as revenus_reels,
            SUM(CASE WHEN t.name = 'Vacant' 
                THEN l.rent_net ELSE 0 END) as perte_vacance,
            SUM(l.rent_net) as revenus_potentiels
        FROM leases l
        LEFT JOIN tenants t ON l.tenant_id = t.id
        WHERE l.status = 'Actif'
    """
    result2 = await db.fetch_one(query2)
    
    calculated = result2['revenus_reels'] + result2['perte_vacance']
    expected = result2['revenus_potentiels']
    difference = abs(calculated - expected)
    
    validations.append({
        "test": "Cohérence: revenus_reels + perte = potentiel",
        "result": round(calculated, 2),
        "expected": round(expected, 2),
        "status": "✅ PASS" if difference < 0.01 else "❌ FAIL",
        "action": "Vérifier calculs" if difference >= 0.01 else None
    })
    
    # Test 3: Tenant "Vacant" existe
    query3 = """
        SELECT COUNT(*) as count
        FROM tenants
        WHERE name = 'Vacant'
    """
    result3 = await db.fetch_one(query3)
    
    validations.append({
        "test": "Tenant 'Vacant' existe dans la base",
        "result": result3['count'],
        "expected": 1,
        "status": "✅ PASS" if result3['count'] == 1 else "❌ FAIL",
        "action": "Créer tenant 'Vacant'" if result3['count'] == 0 else None
    })
    
    return {
        "validation_date": datetime.now().isoformat(),
        "validations": validations,
        "overall_status": "✅ PASS" if all(v['status'] == "✅ PASS" for v in validations) else "❌ FAIL"
    }


# ============================================================================
# HELPER: Créer le tenant "Vacant" si nécessaire
# ============================================================================

async def ensure_vacant_tenant_exists():
    """
    Vérifie que le tenant 'Vacant' existe, le crée sinon.
    À appeler au démarrage du serveur MCP.
    """
    
    query_check = "SELECT id FROM tenants WHERE name = 'Vacant'"
    existing = await db.fetch_one(query_check)
    
    if not existing:
        query_insert = """
            INSERT INTO tenants (id, name, created_at)
            VALUES (gen_random_uuid(), 'Vacant', NOW())
            RETURNING id
        """
        result = await db.fetch_one(query_insert)
        return {
            "created": True,
            "tenant_id": result['id'],
            "message": "Tenant 'Vacant' créé avec succès"
        }
    else:
        return {
            "created": False,
            "tenant_id": existing['id'],
            "message": "Tenant 'Vacant' existe déjà"
        }


# ============================================================================
# TESTS UNITAIRES (à ajouter dans votre suite de tests)
# ============================================================================

import pytest

@pytest.mark.asyncio
async def test_vacant_definition():
    """Vérifie que la définition de vacant est correcte"""
    
    # Créer des données de test
    test_data = pd.DataFrame([
        {'tenant_name': 'Vacant', 'rent_net': 1000, 'expected_vacant': True},
        {'tenant_name': 'John Doe', 'rent_net': 1200, 'expected_vacant': False},
        {'tenant_name': 'Jane Doe', 'rent_net': 0, 'expected_vacant': False},  # Usage interne
    ])
    
    test_data['is_vacant'] = test_data['tenant_name'] == 'Vacant'
    
    for idx, row in test_data.iterrows():
        assert row['is_vacant'] == row['expected_vacant'], \
            f"Row {idx}: Expected vacant={row['expected_vacant']}, got {row['is_vacant']}"


@pytest.mark.asyncio
async def test_financial_vacancy_calculation():
    """Vérifie le calcul de la vacance financière"""
    
    # Données de test
    actual_revenue = 304063.5
    vacancy_loss = 19344.0
    potential_revenue = actual_revenue + vacancy_loss  # 323407.5
    
    # Calcul
    financial_vacancy_pct = (vacancy_loss / potential_revenue) * 100
    
    # Vérification
    expected_pct = 5.98  # Arrondi à 2 décimales
    assert abs(financial_vacancy_pct - expected_pct) < 0.01, \
        f"Expected {expected_pct}%, got {financial_vacancy_pct}%"


@pytest.mark.asyncio
async def test_no_vacant_with_zero_rent():
    """Vérifie qu'aucune unité Vacant n'a rent=0"""
    
    result = await db.fetch_one("""
        SELECT COUNT(*) as count
        FROM leases l
        JOIN tenants t ON l.tenant_id = t.id
        WHERE l.status = 'Actif' 
          AND t.name = 'Vacant' 
          AND l.rent_net = 0
    """)
    
    assert result['count'] == 0, \
        f"Found {result['count']} vacant units with rent=0. They should have theoretical rent > 0."


# ============================================================================
# MIGRATION SCRIPT (si besoin de corriger des données existantes)
# ============================================================================

async def migrate_vacant_units_add_theoretical_rent():
    """
    Script de migration pour ajouter des loyers théoriques aux unités Vacant
    qui ont actuellement rent=0.
    
    ATTENTION: À exécuter manuellement après revue des prix.
    """
    
    # 1. Identifier les unités Vacant sans loyer théorique
    query_identify = """
        SELECT 
            p.name as property_name,
            u.unit_number,
            u.type,
            u.surface_area,
            l.id as lease_id
        FROM leases l
        JOIN units u ON l.unit_id = u.id
        JOIN properties p ON u.property_id = p.id
        JOIN tenants t ON l.tenant_id = t.id
        WHERE l.status = 'Actif'
          AND t.name = 'Vacant'
          AND l.rent_net = 0
    """
    
    units_to_fix = await db.fetch_all(query_identify)
    
    if not units_to_fix:
        return {"message": "Aucune unité à corriger", "units_fixed": 0}
    
    # 2. Pour chaque unité, calculer un loyer théorique basé sur:
    #    - Prix moyen au m² de la propriété
    #    - Prix moyen par type d'unité
    
    fixes_applied = []
    
    for unit in units_to_fix:
        # Calculer loyer théorique
        query_avg = """
            SELECT AVG(l.rent_net / NULLIF(u.surface_area, 0)) as avg_rent_per_sqm
            FROM leases l
            JOIN units u ON l.unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            JOIN tenants t ON l.tenant_id = t.id
            WHERE l.status = 'Actif'
              AND p.name = %(property_name)s
              AND u.type = %(unit_type)s
              AND t.name != 'Vacant'
              AND l.rent_net > 0
              AND u.surface_area > 0
        """
        
        avg_result = await db.fetch_one(query_avg, {
            "property_name": unit['property_name'],
            "unit_type": unit['type']
        })
        
        if avg_result and avg_result['avg_rent_per_sqm']:
            theoretical_rent = round(
                unit['surface_area'] * avg_result['avg_rent_per_sqm'], 
                2
            )
            
            fixes_applied.append({
                "property": unit['property_name'],
                "unit": unit['unit_number'],
                "type": unit['type'],
                "surface": unit['surface_area'],
                "old_rent": 0,
                "new_theoretical_rent": theoretical_rent,
                "calculation": f"{unit['surface_area']} m² × {avg_result['avg_rent_per_sqm']:.2f} CHF/m²"
            })
    
    return {
        "message": f"Identifié {len(fixes_applied)} unités à corriger",
        "fixes_to_apply": fixes_applied,
        "action_required": "Revue manuelle et mise à jour SQL"
    }


# ============================================================================
# NOTES D'INTÉGRATION
# ============================================================================

"""
ÉTAPES D'INTÉGRATION:

1. Backup de l'ancien code
   - Copier get_etat_locatif_complet.py vers get_etat_locatif_complet.py.bak

2. Remplacer la fonction principale
   - Copier la fonction get_etat_locatif_complet() ci-dessus

3. Ajouter la validation (optionnelle)
   - Copier validate_vacancy_data()
   - L'exposer comme nouvel outil MCP si souhaité

4. Tester
   - Appeler l'outil et vérifier les résultats
   - Comparer avec les anciennes valeurs
   - Vérifier que financial_vacancy_pct = 5.98%

5. Mettre à jour la documentation
   - Ajouter les règles métier dans le README
   - Documenter les changements dans CHANGELOG

6. Déployer
   - Commit avec message clair: "fix: correct financial vacancy calculation"
   - Tester en staging avant production
"""
