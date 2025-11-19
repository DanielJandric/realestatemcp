# 🚀 PIPELINE COMPLET - EMBEDDINGS & AGENTIC RAG

## 📋 SCRIPTS CRÉÉS

### 1. **migrate_embeddings.py** ✅
Migrer les 30'854 chunks déjà embedder depuis l'ancien projet

**Status** : Prêt (DRY_RUN = False)  
**Durée** : 2-3 minutes  
**Coût** : 0 USD (réutilisation)

```bash
python migrate_embeddings.py
```

---

### 2. **import_and_embed_all_documents.py** 🆕
Import TOUS les documents restants avec OCR + embeddings

**Fonctionnalités** :
- ✅ Scan automatique OneDriveExport (3'376 fichiers)
- ✅ Filtre fichiers haute valeur (baux, assurances, maintenance, etc.)
- ✅ Azure OCR pour PDFs
- ✅ Extraction Word (.docx, .doc)
- ✅ Extraction Excel (.xlsx, .xls)
- ✅ Chunking intelligent (1000 tokens, 200 overlap)
- ✅ Génération embeddings OpenAI
- ✅ Catégorisation automatique
- ✅ Détection property depuis path
- ✅ Sauvegarde progression (resume capable)
- ✅ Déduplication par hash
- ✅ Tracking coûts en temps réel

**Estimation** :
- Fichiers à traiter : ~3'000-3'500
- Chunks générés : ~50'000
- Durée : 4-6 heures
- Coût : ~65-70 USD

```bash
python import_and_embed_all_documents.py
```

**Note** : Le script peut être interrompu et repris. Progression sauvée dans `embedding_progress.json`

---

### 3. **test_semantic_search.py** 🔍
Test de la recherche sémantique

**Tests automatiques** :
- ✅ Animaux autorisés ?
- ✅ Procédure fuite d'eau ?
- ✅ Clauses indexation ?
- ✅ Contact maintenance chauffage ?
- ✅ Préavis résiliation ?

```bash
python test_semantic_search.py
```

---

### 4. **extract_tenant_contacts.py** 📞
Extraction automatique contacts locataires (TODO 6)

**Fonctionnalités** :
- ✅ Recherche sémantique dans baux
- ✅ Extraction structurée via GPT-4
- ✅ Champs extraits :
  - Téléphone principal
  - Mobile
  - Email
  - Contact d'urgence
  - Garant
- ✅ Update automatique table `tenants`

```bash
python extract_tenant_contacts.py
```

---

## 🎯 PLAN D'EXÉCUTION RECOMMANDÉ

### **Option A : Migration Rapide** (Recommandé si pressé)

```bash
# Étape 1 : Migrer embeddings existants (2 min)
python migrate_embeddings.py

# Étape 2 : Tester recherche (1 min)
python test_semantic_search.py

# Étape 3 : Extraire contacts (5 min)
python extract_tenant_contacts.py

# → Total : ~8 minutes, 0 USD
# → Vous avez 30'854 chunks opérationnels
```

### **Option B : Import Complet** (Recommandé pour setup final)

```bash
# Étape 1 : Migrer embeddings existants (2 min)
python migrate_embeddings.py

# Étape 2 : Import tous les documents (4-6h)
python import_and_embed_all_documents.py

# Étape 3 : Tester recherche (1 min)
python test_semantic_search.py

# Étape 4 : Extraire contacts (5 min)
python extract_tenant_contacts.py

# → Total : 4-6 heures, ~65-70 USD
# → Vous avez ~80'000 chunks (tout le portefeuille)
```

---

## 💰 COÛTS DÉTAILLÉS

| Action | Tokens | Coût | Durée |
|--------|--------|------|-------|
| **Migration existants** | 0 | 0 USD | 2-3 min |
| **Import nouveaux docs** | ~500M | ~65 USD | 4-6h |
| **Test recherche** | ~10K | ~0.001 USD | 1 min |
| **Extract contacts** | ~1M | ~0.15 USD | 5 min |
| **TOTAL** | ~501M | **~65 USD** | **4-6h** |

**Économie vs tout refaire** : ~68 USD + 8h

---

## 📊 CE QUE VOUS OBTENEZ

### Base de Données Enrichie

```sql
-- 80'000+ chunks embedder
SELECT COUNT(*) FROM document_chunks;

-- Recherche sémantique instantanée
SELECT * FROM match_documents(
    query_embedding, 
    match_count := 10
);

-- Contacts locataires extraits
SELECT name, phone, email, emergency_contact 
FROM tenants 
WHERE phone IS NOT NULL;
```

### Capacités Débloquées

✅ **Recherche sémantique** : "Quels baux autorisent animaux ?" → Réponse instantanée  
✅ **Chatbot locataire** : Interface Q&A personnalisée par locataire  
✅ **Agentic RAG** : Agent autonome qui peut agir (emails, alertes, rapports)  
✅ **Extraction auto** : Contacts, clauses, dates, obligations  
✅ **Analyse patterns** : Détection incidents récurrents, opportunités  
✅ **Due diligence** : Génération rapports complets automatiques  
✅ **Compliance** : Audit automatique conformité réglementaire  

---

## 🔧 CONFIGURATION

### Variables d'Environnement (.env)

```env
# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://...
AZURE_DOC_INTELLIGENCE_KEY=...

# Ou Azure Form Recognizer (ancien nom)
AZURE_FORM_RECOGNIZER_ENDPOINT=https://...
AZURE_FORM_RECOGNIZER_KEY=...
```

### Clés API (déjà dans scripts)

- ✅ Supabase URL + Key
- ✅ OpenAI API Key
- ✅ Azure credentials (depuis .env)

---

## 📋 CHECKLIST POST-IMPORT

### Validation

- [ ] Migration embeddings OK (30'854 chunks)
- [ ] Test recherche sémantique fonctionne
- [ ] Contacts locataires extraits
- [ ] (Optionnel) Import complet terminé

### Implémentation

- [ ] Créer fonction RAG (query → context + GPT → answer)
- [ ] Créer agent tools (SQL, email, alerts, etc.)
- [ ] Implémenter LangGraph workflow
- [ ] Créer interface chatbot locataire
- [ ] Setup alertes proactives

### Tests

- [ ] Tester 10 questions variées
- [ ] Valider précision réponses
- [ ] Tester cas edge (aucun résultat, erreurs)
- [ ] Valider performance (<2s par query)

---

## 🚨 TROUBLESHOOTING

### Erreur "Table document_chunks doesn't exist"
```sql
-- Exécuter dans Supabase SQL Editor:
-- create_embeddings_simple.sql
```

### Erreur Azure OCR
```python
# Vérifier .env
AZURE_DOC_INTELLIGENCE_ENDPOINT=...
AZURE_DOC_INTELLIGENCE_KEY=...
```

### OpenAI Rate Limit
```python
# Ajouter dans script:
time.sleep(0.1)  # Entre chaque appel
```

### Script interrompu
```bash
# Relancer, la progression est sauvée
python import_and_embed_all_documents.py
```

---

## 📚 PROCHAINES ÉTAPES

### Immédiat (cette semaine)
1. ✅ Migrer embeddings existants
2. ✅ Tester recherche
3. ✅ Extraire contacts

### Court terme (2-3 semaines)
4. Implémenter RAG simple
5. Créer chatbot locataire MVP
6. Tester avec vrais locataires

### Moyen terme (1-2 mois)
7. Implémenter Agentic RAG
8. Agent autonome avec actions
9. Dashboard analytics
10. Mobile app

---

## 💡 EXEMPLES D'UTILISATION

### Recherche Simple

```python
from supabase import create_client
import openai

# Query
query = "Quels locataires ont clause animaux ?"

# Generate embedding
embedding = openai.embeddings.create(
    model="text-embedding-ada-002",
    input=query
).data[0].embedding

# Search
results = supabase.rpc('match_documents', {
    'query_embedding': embedding,
    'match_count': 5
}).execute()

# → 5 chunks les plus pertinents
```

### RAG Complet

```python
def ask_question(question):
    # 1. Search
    relevant_chunks = semantic_search(question)
    
    # 2. Build context
    context = "\n\n".join([c['chunk_text'] for c in relevant_chunks])
    
    # 3. GPT-4
    answer = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es l'assistant du portefeuille immobilier"},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ]
    ).choices[0].message.content
    
    return answer

# Usage
answer = ask_question("Quels locataires ont clause animaux ?")
```

---

**✅ Tout est prêt ! Lancez `python migrate_embeddings.py` pour commencer ! 🚀**


