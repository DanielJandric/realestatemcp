# RÈGLES MÉTIER - VACANCE ET OCCUPATION

## Définitions officielles

### 1. Unité VACANTE
**Critère unique**: `tenants.name = 'Vacant'`
- Le loyer sur ces unités = **loyer théorique de marché** (pas zéro)
- Ce loyer théorique permet de calculer la perte financière

### 2. Unité OCCUPÉE
**Critères**: `tenants.name != 'Vacant'` ET `leases.rent_net > 0`
- Génère des revenus réels

### 3. Unité à USAGE INTERNE (non-revenue generating)
**Critères**: `tenants.name != 'Vacant'` ET `leases.rent_net = 0`
- Exemples: parkings inclus dans bail commercial, local concierge, local technique, parkings visiteurs
- Ce ne sont PAS des vacances
- Ne génèrent pas de revenus mais sont assignées

## Métriques clés

### Vacance Financière (Financial Vacancy Rate)
```sql
-- FORMULE CORRECTE
SUM(CASE WHEN tenants.name = 'Vacant' THEN leases.rent_net ELSE 0 END) 
/ 
SUM(leases.rent_net) 
* 100

-- Où:
-- Numérateur = loyers théoriques perdus (unités Vacant)
-- Dénominateur = revenus potentiels totaux si 100% occupé
```

### Revenus Réels
```sql
SUM(CASE WHEN tenants.name != 'Vacant' AND leases.rent_net > 0 
    THEN leases.rent_net 
    ELSE 0 END)
```

### Revenus Potentiels (si 100% occupé)
```sql
SUM(leases.rent_net)  -- Inclut les loyers théoriques sur unités Vacant
```

### Taux d'Occupation Physique (Physical Occupancy)
```sql
COUNT(CASE WHEN tenants.name != 'Vacant' THEN 1 END) 
/ 
COUNT(*) 
* 100
```

## ⚠️ ERREURS FRÉQUENTES À ÉVITER

### ❌ FAUX
```sql
-- Ne PAS utiliser rent_net = 0 comme critère de vacance
WHERE rent_net = 0  -- FAUX: inclut usage interne

-- Ne PAS diviser par revenus_réels pour vacance financière
perte / revenus_reels  -- FAUX: dénominateur incorrect
```

### ✅ CORRECT
```sql
-- Utiliser le tenant "Vacant"
WHERE tenants.name = 'Vacant'

-- Diviser par revenus_potentiels
perte / revenus_potentiels
```

## Exemples concrets

### St-Hubert: 34 parkings à rent=0
- Tenant: Radio Rhône, Gilgen, FSCMA, Besucherparkplatz
- Statut: **OCCUPÉS** (usage interne/inclus)
- Vacance financière: **0%**

### Gare 28: Restaurant 326m² avec rent=4'301 CHF
- Tenant: **Vacant**
- rent_net = 4'301 CHF = **loyer théorique perdu**
- Contribue à vacance financière: **Oui**

## Validation des données

### Tests à effectuer
1. Vérifier: `COUNT(tenant='Vacant' AND rent=0)` devrait être 0
2. Vérifier: Tous les Vacant devraient avoir rent_net > 0
3. Vérifier: Somme(revenus_reels) + Somme(loyers_Vacant) = Somme(revenus_potentiels)

---
Date: 2025-11-19
Version: 1.0
