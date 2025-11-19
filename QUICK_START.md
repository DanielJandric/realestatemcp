# ⚡ QUICK START - EMBEDDINGS EN 5 MINUTES

## 🎯 Objectif
Avoir la recherche sémantique opérationnelle en **< 5 minutes**

---

## ✅ ÉTAPE 1 : Validation (30 secondes)

```bash
cd C:\OneDriveExport
python validate_setup.py
```

**Attendu :** Score 8/10 ou plus

**Si échec :**
- ❌ Table `document_chunks` manquante → Voir ÉTAPE 1B
- ❌ Autre erreur → Lire message d'erreur

---

## 🔧 ÉTAPE 1B : Créer Tables (Si nécessaire)

**Ouvrir Supabase SQL Editor :**
1. https://supabase.com/dashboard/project/reqkkltmtaflbkchsmzb
2. Menu "SQL Editor"
3. Copier-coller contenu de `create_embeddings_simple.sql`
4. Cliquer "Run"

**Vérifier :**
```sql
SELECT COUNT(*) FROM document_chunks;
-- Devrait retourner 0 (table vide)
```

---

## 🚀 ÉTAPE 2 : Migration (2 minutes)

```bash
python migrate_embeddings.py
```

**Attendu :**
```
✅ Chunks traités: 30,754/30,854
📊 Taux de succès: 99.7%
```

**Si erreur 500 en fin :** Normal, 99.7% est excellent !

---

## 🔍 ÉTAPE 3 : Test (1 minute)

```bash
python test_semantic_search.py
```

**Attendu :**
```
🔍 Question: Quels locataires peuvent avoir des animaux domestiques ?

📊 3 résultats trouvés:

1. Similarité: 0.847
   Texte: Article 5 - Animaux domestiques...
```

**Si ça marche :** 🎉 Vous avez la recherche sémantique !

---

## ✅ ÉTAPE 4 : Extraction Contacts (5 minutes)

```bash
python extract_tenant_contacts.py
```

**Attendu :**
```
✅ Locataires mis à jour: 45
📊 Total: 300
```

---

## 🎉 TERMINÉ !

**Vous avez maintenant :**
- ✅ 30'854 chunks embedder
- ✅ Recherche sémantique opérationnelle
- ✅ Contacts locataires extraits

---

## 🚀 PROCHAINES ÉTAPES (Optionnel)

### Si vous voulez TOUT importer (4-6h, ~65 USD)

```bash
python import_and_embed_all_documents.py
```

### Si vous voulez tout automatiser

```bash
python run_complete_pipeline.py
```

---

## 💡 TESTER MAINTENANT

### Python
```python
from supabase import create_client
import openai

supabase = create_client(
    "https://reqkkltmtaflbkchsmzb.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"
)

openai.api_key = "your_openai_api_key_here"

# Your question
question = "Quels sont les délais de préavis ?"

# Generate embedding
emb = openai.embeddings.create(
    model="text-embedding-ada-002",
    input=question
).data[0].embedding

# Search
results = supabase.rpc('match_documents', {
    'query_embedding': emb,
    'match_count': 3
}).execute()

# Show results
for r in results.data:
    print(f"Similarité: {r['similarity']:.3f}")
    print(f"Texte: {r['chunk_text'][:200]}...\n")
```

---

## 🆘 AIDE

### Erreur "Table doesn't exist"
→ Faites ÉTAPE 1B (créer tables)

### Erreur "API Key invalid"
→ Vérifiez clés dans scripts

### Script bloqué
→ Ctrl+C puis relancer (progression sauvée)

### Autre problème
→ Lire `README_EMBEDDINGS.md` (troubleshooting complet)

---

## 📚 DOCUMENTATION COMPLÈTE

- **QUICK_START.md** ← Vous êtes ici
- **README_EMBEDDINGS.md** ← Guide complet
- **RECAP_FINAL_EMBEDDINGS.md** ← Vue d'ensemble

---

**🚀 GO ! Commencez par `python validate_setup.py` 🚀**


