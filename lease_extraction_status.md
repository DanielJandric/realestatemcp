# 📄 Extraction Exhaustive des Baux à Loyer

## Statut Actuel

**Script lancé**: `comprehensive_lease_extraction.py` (en arrière-plan)

**Progression**: 35/326 PDFs traités

## Objectifs

### ✅ Phase 1: Extraction des PDFs (EN COURS)
- [x] Scanner tous les dossiers "Baux à loyer"
- [x] Identifier 326 baux actifs (hors "Anciens baux")
- [x] Configurer Azure OCR
- [ ] Extraire le texte de tous les PDFs (35/326 complétés)
- [ ] Parser les informations clés:
  - Type d'unité (appartement, bureau, commerce, parking, cave, restaurant, atelier)
  - Nombre de pièces
  - Surface (m²)
  - Étage
  - Loyer net
  - Charges
- [ ] Uploader tous les PDFs dans la table `documents`

### ⏳ Phase 2: Enrichissement de la base
- [ ] Mettre à jour les 463 `units` avec les types détectés
- [ ] Compléter les informations manquantes (pièces, surface, étage)
- [ ] Lier chaque `document` au bon `lease_id`
- [ ] Mettre à jour les `tenants` avec coordonnées extraites

### ⏳ Phase 3: Vérification
- [ ] Vérifier que chaque `lease` actif a son bail PDF
- [ ] Confirmer la diversité des types d'unités (≠ juste appartements/parkings)
- [ ] Statistiques finales

## Résultats Attendus

**Avant**:
- 463 units avec `unit_type = None`
- 2 catégories seulement (appartements/parkings)
- Aucun bail PDF uploadé

**Après**:
- 463 units avec types précis (7+ catégories)
- ~326 baux PDF uploadés et liés
- Informations complètes (pièces, surface, étage)
- Données tenants enrichies

## Commandes

### Vérifier la progression
```powershell
Get-Content lease_extraction_progress.json | ConvertFrom-Json
```

### Voir les documents uploadés
```powershell
python -c "from supabase import create_client; s=create_client('https://reqkkltmtaflbkchsmzb.supabase.co','...');  print(s.table('documents').select('*',count='exact').filter('category','eq','lease').execute().count)"
```

### Reprendre l'extraction (si interrompue)
```powershell
python comprehensive_lease_extraction.py
```

## Notes

- L'extraction prend ~2-3 secondes par PDF (Azure OCR)
- Temps estimé total: ~15-20 minutes pour les 326 PDFs
- La progression est sauvegardée tous les 5 fichiers
- Le script peut être interrompu (Ctrl+C) et reprendra automatiquement

## Problèmes Connus

1. **Matching des propriétés**: Certains PDFs dans des dossiers génériques nécessitent un matching amélioré
2. **Quality OCR**: PDFs scannés de mauvaise qualité peuvent donner des résultats incomplets
3. **Parsing heuristique**: La détection du type d'unité se base sur des mots-clés (peut nécessiter ajustements)

## Structure de Données

### Table `documents`
```sql
- id: UUID
- property_id: UUID (FK)
- lease_id: UUID (FK) -- À ajouter en Phase 2
- file_path: TEXT
- file_name: TEXT
- file_type: 'pdf'
- category: 'lease'
```

### Table `units` (enrichie)
```sql
- unit_type: TEXT -- appartement|bureau|commerce|parking|cave|restaurant|atelier
- rooms: NUMERIC -- Nombre de pièces
- surface_area: NUMERIC -- m²
- floor: INTEGER -- Étage
```


