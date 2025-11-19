# 📋 IMPORT CONTRATS DE MAINTENANCE - STATUT

**Date**: 19 novembre 2025  
**Statut**: ⏳ EN ATTENTE DE CRÉATION TABLE

---

## ✅ ACCOMPLI

### 1. Fichiers Identifiés
**6 fichiers** de contrats d'entretien trouvés :
- ✅ Gare 8-10 Martigny (16 contrats)
- ✅ Gare 28 Sion (18 contrats)
- ✅ Place Centrale 3 Martigny (14 contrats)
- ⏸️ Grande-Avenue 6 Chippis (en attente)
- ⏸️ Pratifori 5-7 Sion (en attente)
- ⏸️ Banque 4 Fribourg (en attente)

### 2. Structure Analysée
**Colonnes identifiées** :
1. **Nom d'entreprise** → `vendor_name`
2. **Objet** → `description` + `contract_type`
3. **Nombre d'intervention** → `frequency`
4. **Total HT/an** → `annual_cost`
5. **Début du contrat** → `start_date`
6. **Préavis de résiliation** → `notice_period`
7. **Fin du contrat possible** → `end_date`
8. **Etat actuel** → `status` (active, terminated, to_terminate)
9. **Remarques Investis** → ajouté dans `description`
10. **Remarques Gérance** → ajouté dans `description`

### 3. Données Extraites (3 premiers fichiers)
**48 contrats** identifiés et prêts à l'import :

#### Par Type
- Ventilation : 8
- Toiture : 7
- Conciergerie : 4
- Ascenseur : 4
- Chaufferie : 3
- Maintenance : 3
- Extincteurs : 2
- Buanderie : 2
- Autres : 15

#### Par Statut
- **Actifs** : 41 contrats
- **À résilier** : 5 contrats
- **Résiliés** : 2 contrats

#### Coûts Annuels
- **Total** : 116'618.30 CHF/an
- **Actifs** : 67'005.90 CHF/an

---

## ⏳ EN ATTENTE

### Étape Actuelle : Création Table Maintenance

**Fichier SQL créé** : `create_maintenance_table.sql`

**À exécuter dans Supabase SQL Editor** :

```sql
CREATE TABLE IF NOT EXISTS maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    unit_id UUID REFERENCES units(id) ON DELETE SET NULL,
    vendor_name TEXT NOT NULL,
    contract_type TEXT,
    description TEXT,
    annual_cost NUMERIC(10,2),
    frequency TEXT,
    start_date DATE,
    end_date DATE,
    notice_period TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
```

---

## 📊 APRÈS CRÉATION TABLE

### Prochaines Actions Automatiques

1. **Import des 48 contrats** (3 fichiers déjà parsés)
2. **Import des 3 fichiers restants** (avec gestion 11 colonnes)
3. **Vérification données** :
   - Propriétés correctement liées
   - Dates valides
   - Coûts formatés
   - Statuts cohérents

### Améliorations Possibles

- **Linkage aux unités** : Associer certains contrats à des unités spécifiques
- **Alertes expiration** : Détecter les contrats qui arrivent à échéance
- **Calcul revenus nets** : Soustraire maintenance du revenu locatif
- **Documents** : Lier les PDF de contrats depuis dossiers

---

## 🔧 SCRIPTS CRÉÉS

### Scripts Principaux
1. **`inspect_maintenance_files.py`** - Analyse structure Excel
2. **`inspect_maintenance_detailed.py`** - Détection header row
3. **`import_maintenance_contracts.py`** - Import complet ✅
4. **`create_maintenance_table.sql`** - Création table ⏸️

### Fonctionnalités Implémentées
- ✅ Lecture Excel multi-formats (10 et 11 colonnes)
- ✅ Parsing dates multiples formats
- ✅ Nettoyage coûts (virgules, espaces, quotes)
- ✅ Détection statuts (actif, résilié, à résilier)
- ✅ Association automatique aux propriétés
- ✅ Fusion remarques dans description
- ✅ Insert par batch (50 contrats à la fois)

---

## 📈 IMPACT ATTENDU

### Business Intelligence
- **Visibilité complète** des coûts de maintenance
- **Budget annuel** : ~116'618 CHF identifiés
- **Optimisation** : 5 contrats à résilier détectés
- **Suivi expirations** : Dates de fin capturées

### Gestion Opérationnelle
- Calendrier des interventions
- Liste prestataires consolidée
- Historique contrats par propriété
- Alertes renouvellement

---

## ✅ COMMANDES POUR CONTINUER

Une fois `create_maintenance_table.sql` exécuté :

```bash
python import_maintenance_contracts.py
```

Cela va :
1. Réimporter les 3 premiers fichiers (48 contrats)
2. Traiter les 3 fichiers restants
3. Afficher statistiques complètes

---

*En attente de création table dans Supabase...*


