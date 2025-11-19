# 📄 Rapport d'Extraction des Baux à Loyer

## 🎯 Objectif

Extraire **TOUS les baux signés** (326 PDFs) et utiliser les données pour:
1. Compléter la table `units` avec types détaillés
2. Enrichir la table `tenants` avec coordonnées
3. Uploader chaque bail PDF signé
4. Lier chaque document au bon `lease`

## 📊 État Actuel (en cours d'extraction)

### Progression
- **Traités**: 65/326 PDFs (~20%)
- **Uploadés**: 47 documents
- **Taux de succès**: ~72%

### Avant l'extraction
```
Units:
- Total: 463
- Types: 1 catégorie (None: 463)
- ❌ Impossible d'avoir que 2 catégories (appartements/parkings)

Tenants:
- Total: 225
- Coordonnées: Incomplètes

Documents:
- Baux signés: 0
- ❌ Aucun bail uploadé
```

### Après l'extraction (attendu)
```
Units:
- Total: 463
- Types: 7+ catégories
  - Appartements: ~200-250
  - Bureaux: ~50-80
  - Commerces: ~30-50
  - Parkings: ~50-70
  - Caves: ~10-20
  - Restaurants: ~5-10
  - Ateliers: ~5-10
- ✅ Informations complètes: pièces, surface, étage

Tenants:
- Total: 225
- ✅ Coordonnées enrichies (email, téléphone)

Documents:
- Baux signés: ~300-326
- ✅ Chaque lease a son bail PDF
- ✅ Liens lease_id établis
```

## 🔍 Types d'Unités Détectés

Le script identifie automatiquement 7 catégories via mots-clés:

| Type | Mots-clés | Exemples |
|------|-----------|----------|
| **Appartement** | appartement, logement, habitation | 2.5 pièces, 3.5 pièces |
| **Bureau** | bureau, office, büro | Cabinet médical, Bureau avocat |
| **Commerce** | commerce, magasin, boutique, arcade | Manor, McDonald's, Fielmann |
| **Parking** | parking, place de parc, garage, PP | Box, Place extérieure |
| **Cave** | cave, dépôt, storage, lager | Cave privée, Dépôt |
| **Restaurant** | restaurant, café, bar | Bar, Brasserie |
| **Atelier** | atelier, workshop | Atelier artisan |

## 📋 Données Extraites de Chaque Bail

Pour chaque PDF, le script OCR Azure extrait:

### Informations Unité
- ✅ Type d'unité (7 catégories)
- ✅ Nombre de pièces (1.5, 2.5, 3.5, etc.)
- ✅ Surface (m²)
- ✅ Étage (RDC, 1er, 2ème, etc.)
- ✅ Référence (ex: 45638.02.440050)

### Informations Financières
- ✅ Loyer net (CHF)
- ✅ Charges (CHF)

### Informations Tenant
- ✅ Nom complet
- ✅ Email (si présent)
- ✅ Téléphone (si présent)
- ✅ Dates (début/fin)

## 🚀 Scripts Créés

### 1. `fast_lease_extraction.py` (EN COURS)
- Extrait les 326 baux avec Azure OCR
- Upload dans `documents` avec `category='lease'`
- Matching intelligent des propriétés
- Progression sauvegardée (reprend automatiquement)

### 2. `enrich_units_and_tenants.py` (À EXÉCUTER APRÈS)
- Met à jour les 463 units avec les types détectés
- Complète pièces, surface, étage
- Enrichit les 225 tenants avec coordonnées
- Lie chaque document au bon lease_id

### 3. `verify_completeness.py` (VÉRIFICATION FINALE)
- Vérifie que chaque lease actif a son bail
- Statistiques par type d'unité
- Rapport de complétude

## ⏱️ Timeline

| Étape | Durée estimée | Statut |
|-------|---------------|--------|
| Extraction 326 PDFs | ~15-20 min | 🔄 EN COURS (20% fait) |
| Enrichissement tables | ~2-3 min | ⏳ En attente |
| Vérification | ~1 min | ⏳ En attente |
| **TOTAL** | **~20-25 min** | |

## 📈 Métriques de Succès

### Critères de Validation
- [x] Scanner tous les dossiers "Baux à loyer"
- [ ] Extraire ≥ 300 baux (sur 326 trouvés)
- [ ] Uploader ≥ 300 PDFs dans `documents`
- [ ] Identifier ≥ 5 types d'unités différents
- [ ] Enrichir 100% des units avec type
- [ ] Lier ≥ 90% des documents aux leases

### KPIs
- **Couverture**: % de leases avec bail PDF
- **Diversité**: Nombre de catégories d'unités
- **Qualité**: % d'unités avec infos complètes (type + surface + pièces)

## 🔧 Améliorations Techniques

### Matching des Propriétés
- ✅ Lookup par nom normalisé
- ✅ Lookup par référence (45638, 45634, etc.)
- ✅ Fallback sur mots-clés multiples
- ✅ Map manuel des références connues

### Rate Limiting Azure
- ✅ 0.3s entre requêtes
- ✅ Gestion des erreurs et retry
- ✅ Sauvegarde tous les 10 fichiers

### Reprise Automatique
- ✅ Fichier de progression JSON
- ✅ Skip des fichiers déjà traités
- ✅ Interruptible (Ctrl+C)

## 📝 Prochaines Étapes

1. **Attendre fin extraction** (~10-15 min restants)
   ```powershell
   Get-Content lease_extraction_progress.json | ConvertFrom-Json
   ```

2. **Exécuter enrichissement**
   ```powershell
   python enrich_units_and_tenants.py
   ```

3. **Vérifier complétude**
   ```powershell
   python verify_completeness.py
   ```

4. **Valider résultats**
   - Diversité des types d'unités ✅
   - Chaque lease a son bail ✅
   - Données complètes ✅

## 🎉 Résultat Final Attendu

```sql
SELECT 
    unit_type, 
    COUNT(*) as count,
    ROUND(AVG(rooms), 1) as avg_rooms,
    ROUND(AVG(surface_area), 0) as avg_surface
FROM units
WHERE unit_type IS NOT NULL
GROUP BY unit_type
ORDER BY count DESC;
```

| unit_type | count | avg_rooms | avg_surface |
|-----------|-------|-----------|-------------|
| appartement | 245 | 3.2 | 85 |
| bureau | 68 | - | 45 |
| commerce | 42 | - | 120 |
| parking | 65 | - | 15 |
| cave | 18 | - | 12 |
| restaurant | 8 | - | 180 |
| atelier | 17 | - | 95 |

---

*Extraction lancée le: 2025-11-19*
*Statut: EN COURS (20% complété)*


