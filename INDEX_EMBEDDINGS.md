# 📚 INDEX - EMBEDDINGS & AGENTIC RAG

## 🚀 DÉMARRAGE RAPIDE

| Fichier | Type | Description |
|---------|------|-------------|
| **QUICK_START.md** | 📖 Doc | Guide 5 minutes pour démarrer |
| **validate_setup.py** | 🐍 Script | Vérifier que tout est prêt |

**→ Commencez par :** `python validate_setup.py`

---

## 📖 DOCUMENTATION

| Fichier | Taille | Description |
|---------|--------|-------------|
| **QUICK_START.md** | ⭐⭐⭐ | Guide rapide 5 min |
| **README_EMBEDDINGS.md** | ⭐⭐⭐⭐⭐ | Guide complet avec tout |
| **RECAP_FINAL_EMBEDDINGS.md** | ⭐⭐⭐⭐ | Récapitulatif final |
| **INDEX_EMBEDDINGS.md** | ⭐⭐ | Ce fichier (index) |

---

## 🐍 SCRIPTS PRINCIPAUX

### Migration & Import

| Script | Durée | Coût | Priority |
|--------|-------|------|----------|
| **migrate_embeddings.py** | 2-3 min | 0 USD | ⭐⭐⭐ HIGH |
| **import_and_embed_all_documents.py** | 4-6h | ~65 USD | ⭐⭐ MEDIUM |
| **run_complete_pipeline.py** | 4-6h | ~65 USD | ⭐ LOW |

### Tests & Extraction

| Script | Durée | Coût | Priority |
|--------|-------|------|----------|
| **test_semantic_search.py** | 1 min | ~0 USD | ⭐⭐⭐ HIGH |
| **extract_tenant_contacts.py** | 5 min | ~0.15 USD | ⭐⭐ MEDIUM |
| **validate_setup.py** | 30s | 0 USD | ⭐⭐⭐ HIGH |

---

## 🗄️ SCRIPTS SQL

| Script | Type | Description |
|--------|------|-------------|
| **create_embeddings_simple.sql** | Setup | Créer tables + fonction search |
| **create_embeddings_tables.sql** | Setup | Version complète (alternative) |
| **create_documents_table.sql** | Setup | Table documents + views |

**→ Exécuter dans :** Supabase SQL Editor

---

## 📊 TABLES CRÉÉES

| Table/View | Contenu | Taille |
|------------|---------|--------|
| **document_chunks** | Chunks + embeddings | ~80'000 rows |
| **documents** | Registry fichiers | ~3'500 rows |
| **vw_document_stats** | Stats par catégorie | View |
| **vw_documents_by_property** | Docs par propriété | View |

**Fonction SQL :**
- `match_documents(embedding, count)` → Recherche sémantique

---

## 🎯 WORKFLOWS

### Workflow 1 : Setup Rapide (5 min)
```
validate_setup.py
  ↓
create_embeddings_simple.sql (si nécessaire)
  ↓
migrate_embeddings.py
  ↓
test_semantic_search.py
```

### Workflow 2 : Setup Complet (4-6h)
```
validate_setup.py
  ↓
create_embeddings_simple.sql
  ↓
run_complete_pipeline.py
  (fait tout automatiquement)
```

### Workflow 3 : Import Incrémental
```
migrate_embeddings.py (déjà fait)
  ↓
import_and_embed_all_documents.py
  (ajoute nouveaux docs)
  ↓
test_semantic_search.py (vérifier)
```

---

## 💰 COÛTS

| Action | Coût |
|--------|------|
| Migration embeddings existants | 0 USD |
| Import complet nouveaux docs | ~65 USD |
| Test recherche | ~0 USD |
| Extract contacts | ~0.15 USD |
| Query recherche (unit) | ~0.0003 USD |
| **Setup complet** | **~65 USD** |
| **Maintenance mensuelle** | **~15 USD** |

---

## ⏱️ DURÉES

| Action | Durée |
|--------|-------|
| Validation | 30s |
| Migration | 2-3 min |
| Test recherche | 1 min |
| Extract contacts | 5 min |
| Import complet | 4-6h |
| **Setup rapide** | **~5 min** |
| **Setup complet** | **~4-6h** |

---

## 📋 CHECKLIST

### Phase 1 : Setup (5 min)
- [ ] `python validate_setup.py` → Score 8+/10
- [ ] Exécuter `create_embeddings_simple.sql` si nécessaire
- [ ] `python migrate_embeddings.py` → 30'854 chunks
- [ ] `python test_semantic_search.py` → Résultats OK

### Phase 2 : Validation (5 min)
- [ ] Tester 5 questions différentes
- [ ] Vérifier similarité > 0.7
- [ ] `python extract_tenant_contacts.py`
- [ ] Vérifier contacts dans table `tenants`

### Phase 3 : Import Complet (Optionnel, 4-6h)
- [ ] `python import_and_embed_all_documents.py`
- [ ] Monitoring progression (`embedding_progress.json`)
- [ ] Vérifier coûts OpenAI dashboard
- [ ] Re-tester recherche

### Phase 4 : Production (À venir)
- [ ] Implémenter RAG complet
- [ ] Créer chatbot locataire
- [ ] Dashboard analytics
- [ ] Agentic RAG avec LangGraph

---

## 🔑 CREDENTIALS

**Inclus dans scripts :**
- ✅ Supabase URL
- ✅ Supabase Service Role Key
- ✅ OpenAI API Key

**À configurer (.env) :**
- ⚠️ Azure Document Intelligence Endpoint
- ⚠️ Azure Document Intelligence Key

---

## 📊 STATISTIQUES ACTUELLES

### Base Actuelle
```
Properties:          8
Units:             462
Leases:            366
Tenants:          ~300
Maintenance:        34
Insurance:          10
Financial Stmt:     96
```

### Après Embeddings
```
+ Documents:      ~3'500
+ Chunks:         30'854 (migration)
              + ~50'000 (import complet)
              = ~80'000 TOTAL
```

---

## 🎯 CAPACITÉS

### Actuel
- ✅ CRUD complet (properties, units, leases, etc.)
- ✅ Vues matérialisées
- ✅ Indexes optimisés
- ✅ RLS configuré

### Après Setup Rapide (5 min)
- ✅ Recherche sémantique
- ✅ 30'854 chunks disponibles
- ✅ Contacts extraits

### Après Import Complet (4-6h)
- ✅ ~80'000 chunks
- ✅ Couverture exhaustive
- ✅ Multi-documents
- ✅ Foundation Agentic RAG

---

## 🚨 TROUBLESHOOTING

| Problème | Solution | Doc |
|----------|----------|-----|
| Table manquante | `create_embeddings_simple.sql` | README |
| API Key invalide | Vérifier scripts | README |
| Script bloqué | Ctrl+C puis relancer | README |
| Erreur 500 | Normal en fin (99.7% OK) | README |
| Azure manquant | Fallback PyPDF2 activé | README |

---

## 📞 SUPPORT

1. **Validation** → `python validate_setup.py`
2. **Quick Start** → Lire `QUICK_START.md`
3. **Guide Complet** → Lire `README_EMBEDDINGS.md`
4. **Troubleshooting** → Section dans README

---

## 🎉 NEXT STEPS

### Immédiat
1. Lancer `python validate_setup.py`
2. Lancer `python migrate_embeddings.py`
3. Tester recherche

### Court Terme
4. Implémenter RAG simple
5. Créer chatbot MVP
6. Tester avec utilisateurs

### Moyen Terme
7. Import complet (optionnel)
8. Agentic RAG
9. Dashboard
10. Mobile app

---

**🚀 START HERE: `python validate_setup.py` 🚀**

**📖 THEN READ: `QUICK_START.md` 📖**

**🎯 GOAL: Recherche sémantique en 5 min 🎯**


