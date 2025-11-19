# 🏢 Real Estate Intelligence System

**Assistant immobilier intelligent pour Claude Desktop via MCP (Model Context Protocol)**

Système de gestion immobilière avec IA, recherche sémantique et analyse automatique - conçu pour fonctionner en LOCAL avec Claude Desktop.

## ⭐ Usage Principal: Claude Desktop + MCP

Ce projet expose **7 outils sophistiqués** à Claude Desktop pour interroger votre base de données immobilière en temps réel.

**→ Guide de démarrage: [QUICK_START_CLAUDE.md](QUICK_START_CLAUDE.md)**

## 🚀 Fonctionnalités

- **31,605 chunks** avec embeddings AI (OpenAI text-embedding-ada-002)
- **7 outils MCP** pour Claude Desktop (recherche sémantique, analytics, comparaisons)
- **Recherche sémantique** en langage naturel sur tous les documents
- **Extraction automatique** des servitudes depuis registre foncier
- **Analytics** avancés (dashboards propriétés, finances, contrats)
- **8 propriétés** complètement enrichies
- **100% Local** - Aucun serveur nécessaire

## 📊 Données

- ✅ 653+ documents centralisés (baux, assurances, maintenance)
- ✅ 68 extraits registre foncier avec OCR
- ✅ 463 unités typées (appartements, parkings, bureaux)
- ✅ 95 baux enrichis
- ✅ Servitudes et restrictions automatiquement extraites
- ✅ États financiers par propriété

## 🔧 Stack Technique

- **Database:** Supabase (PostgreSQL + pgvector)
- **Embeddings:** OpenAI API (text-embedding-ada-002)
- **OCR:** Azure Document Intelligence
- **Backend:** Python 3.11+
- **Deployment:** Render (optionnel)

## 📦 Installation

### Prérequis

```bash
Python 3.11+
pip
```

### Setup Local

```bash
# Clone le repo
git clone <your-repo-url>
cd <repo-name>

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Éditer .env avec vos clés
```

### Variables d'Environnement

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_service_role_key

# OpenAI
OPENAI_API_KEY=sk-proj-xxx

# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://xxx.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=xxx
```

## 🎯 Utilisation

### 1. Recherche Sémantique

```python
from supabase import create_client
import openai

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Générer embedding
query = "contrats de maintenance coûteux"
embedding = openai.embeddings.create(
    input=query,
    model="text-embedding-ada-002"
).data[0].embedding

# Recherche
results = supabase.rpc('match_documents', {
    'query_embedding': embedding,
    'match_threshold': 0.7,
    'match_count': 10
}).execute()
```

### 2. Analyse Servitudes

```bash
python analyze_servitudes.py
```

### 3. Dashboard Propriétés

```sql
SELECT * FROM vw_servitudes_summary;
```

### 4. Tests

```bash
python test_semantic_search.py
python check_embedding_progress.py
```

## 📋 Scripts Disponibles

### Import & Processing
- `embed_delta_only.py` - Import nouveaux documents + embeddings
- `import_land_registry_with_ocr.py` - Import registre foncier
- `link_all_chunks_complete.py` - Linking chunks → propriétés

### Analysis
- `analyze_servitudes.py` - Analyse servitudes et restrictions
- `check_embedding_progress.py` - État des embeddings
- `final_status_report.py` - Rapport complet système

### Testing
- `test_semantic_search.py` - Tests recherche basique
- `test_semantic_search_advanced.py` - Tests avec filtres

## 🗄️ Structure Database

### Tables Principales
- `properties` - 8 immeubles avec données financières
- `units` - 463 unités typées
- `leases` - 95 baux enrichis
- `tenants` - 225 locataires
- `maintenance` - Contrats entretien
- `insurance_policies` - Polices assurance
- `servitudes` - Servitudes et restrictions
- `land_registry_documents` - Extraits RF
- `document_chunks` - 31,605 chunks avec embeddings
- `documents` - Registry central

### Vues
- `vw_servitudes_summary` - Résumé servitudes par propriété
- `vw_document_stats` - Statistiques documents
- `vw_documents_by_property` - Distribution docs

## 🔍 Exemples de Requêtes

### Servitudes Critiques
```sql
SELECT 
    p.name,
    s.type_servitude,
    s.description,
    s.impact_constructibilite
FROM servitudes s
JOIN properties p ON p.id = s.property_id
WHERE s.importance_niveau = 'critique'
  AND s.statut = 'active';
```

### Rentabilité par Propriété
```sql
SELECT 
    p.name,
    p.total_annual_rent as revenue,
    SUM(m.annual_cost) as costs,
    p.total_annual_rent - COALESCE(SUM(m.annual_cost), 0) as net
FROM properties p
LEFT JOIN maintenance m ON m.property_id = p.id
GROUP BY p.id, p.name, p.total_annual_rent
ORDER BY net DESC;
```

### Recherche Filtrée
```sql
SELECT 
    chunk_text,
    metadata->>'file_name' as file,
    metadata->>'property_name' as property
FROM document_chunks
WHERE metadata->>'property_name' = 'Pratifori 5-7'
  AND metadata->>'category' = 'lease'
LIMIT 10;
```

## 🤖 MCP Integration

Scripts MCP disponibles dans `/mcp_tools/`:
- `semantic_search_mcp.py` - Recherche sémantique via MCP
- `property_analytics_mcp.py` - Analytics propriétés
- `servitudes_analysis_mcp.py` - Analyse servitudes
- `complex_queries_mcp.py` - Requêtes complexes

Voir `MCP_INTEGRATION.md` pour détails.

## 📚 Documentation

- `GUIDE_COMPLET_FINAL.md` - Guide complet d'utilisation
- `CAPACITES_FINALES_SYSTEME.md` - Liste des capacités
- `ETAT_FINAL_EMBEDDINGS.md` - État embeddings
- `START_HERE_FINAL.txt` - Quick start

## 🚢 Déploiement Render

```bash
# Via render.yaml (auto-deploy)
git push origin main

# Ou manuel via CLI
render deploy
```

Voir `render.yaml` pour configuration.

## 📊 Statistiques

- **Chunks:** 31,605 (dont ~18,000 liés à propriétés)
- **Documents:** 653+
- **Propriétés:** 8
- **Servitudes:** Extraites automatiquement
- **Taux de linking:** ~77%
- **Coût embeddings:** ~$5 total

## 🔐 Sécurité

- ✅ RLS (Row Level Security) activé sur toutes tables
- ✅ Service role pour scripts automatiques
- ✅ Variables d'environnement pour secrets
- ⚠️ Ne jamais commit `.env` ou clés API

## 🤝 Contribution

Ce projet est privé. Pour questions ou suggestions:
1. Créer une issue
2. Proposer PR avec description détaillée

## 📝 License

Propriétaire - Tous droits réservés

## 🎯 Roadmap

- [ ] Interface web de recherche
- [ ] API REST publique
- [ ] Dashboards interactifs
- [ ] Agentic RAG complet
- [ ] Chatbot locataires
- [ ] Analyse prédictive ML
- [ ] Mobile app

## 💡 Support

Pour aide ou questions:
- Consulter `GUIDE_COMPLET_FINAL.md`
- Lancer `LANCER_ANALYSE.bat` pour diagnostics
- Vérifier logs dans `/terminals/`

---

**Version:** 1.0 PRODUCTION  
**Status:** ✅ Opérationnel  
**Last Updated:** 2025-11-19

