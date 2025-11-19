# 🚀 Guide de Déploiement

## 📋 Pré-requis

✅ Environnement Render déjà configuré  
✅ Repository GitHub prêt  
✅ Variables d'environnement sur Render

## 🔧 Étape 1: Préparer le Push GitHub

### Vérifier les fichiers

```bash
# Voir ce qui sera commité
git status

# Fichiers importants à inclure:
# - README.md
# - requirements.txt
# - render.yaml
# - mcp_tools/
# - Scripts Python (*.py)
# - Documentation (*.md)
# - SQL (*.sql)

# Fichiers exclus (via .gitignore):
# - .env
# - OneDriveExport/
# - *.pdf, *.docx
# - terminals/
# - progress files
```

### Commandes Git

```bash
# Initialiser si nécessaire
git init

# Ajouter remote
git remote add origin <your-github-url>

# Ajouter fichiers
git add .

# Commit
git commit -m "Initial commit: Real Estate Intelligence System

- 31,605 embeddings chunks
- Semantic search capability
- Land registry & servitudes extraction
- 8 properties fully enriched
- MCP tools for advanced analytics
- Complete documentation"

# Push
git push -u origin main
```

## 📦 Étape 2: Configuration Render

### Variables d'Environnement (Déjà configurées)

Sur Render Dashboard → Service → Environment:

```
SUPABASE_URL=https://reqkkltmtaflbkchsmzb.supabase.co
SUPABASE_KEY=eyJhbGc...
OPENAI_API_KEY=sk-proj-...
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://...
AZURE_DOC_INTELLIGENCE_KEY=...
DATABASE_URL=postgresql://...  (pour MCP)
```

### Services Render

#### Option A: Worker Service (Background Jobs)
```yaml
# render.yaml déjà configuré
Type: Worker
Name: real-estate-embeddings
Command: python -u embed_delta_only.py
Auto-deploy: No (manuel uniquement)
```

#### Option B: Web Service (API - Future)
```yaml
Type: Web
Name: real-estate-api
Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Auto-deploy: Yes
```

## 🎯 Étape 3: Déploiement

### Auto-deploy via GitHub

```bash
# Après git push, Render détecte automatiquement
git push origin main

# Render va:
# 1. Détecter render.yaml
# 2. Créer/mettre à jour services
# 3. Installer requirements.txt
# 4. Démarrer services configurés
```

### Manuel via Dashboard

1. Aller sur dashboard.render.com
2. Sélectionner le service
3. Cliquer "Manual Deploy" → "Deploy latest commit"
4. Suivre les logs

## 🔍 Étape 4: Vérification Post-Déploiement

### Vérifier Logs

```bash
# Via CLI Render
render logs -s real-estate-embeddings --tail

# Ou Dashboard → Service → Logs
```

### Tests de Santé

```python
# Script de test à exécuter
python -c "
from supabase import create_client
import os

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Test connection
result = supabase.table('document_chunks').select('id', count='exact').execute()
print(f'✅ Database OK: {result.count} chunks')

# Test OpenAI
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
response = openai.embeddings.create(model='text-embedding-ada-002', input='test')
print('✅ OpenAI OK')
"
```

## 🤖 Étape 5: Configuration MCP

### MCP a accès via DATABASE_URL

Les outils MCP dans `/mcp_tools/` utilisent automatiquement `DATABASE_URL`:

```python
# MCP peut directement appeler:
from mcp_tools.semantic_search_mcp import semantic_search
from mcp_tools.property_analytics_mcp import get_property_dashboard

# Exemples:
results = semantic_search("contrats maintenance")
dashboard = get_property_dashboard("Pratifori 5-7")
financial = get_financial_summary()
```

### Fonctions Disponibles pour MCP

**Recherche Sémantique:**
- `semantic_search()` - Recherche documents
- `search_servitudes()` - Recherche servitudes
- `multi_source_search()` - Multi-source

**Analytics:**
- `get_property_dashboard()` - Dashboard propriété
- `compare_properties()` - Comparaison
- `get_expiring_leases()` - Baux expirants
- `get_servitudes_by_importance()` - Servitudes critiques
- `get_maintenance_summary()` - Contrats maintenance
- `get_financial_summary()` - Vue financière globale

### Test MCP Integration

```python
# Test complet MCP
python mcp_tools/semantic_search_mcp.py
python mcp_tools/property_analytics_mcp.py

# Devrait afficher résultats de tests
```

## 📊 Étape 6: Monitoring

### Métriques à Surveiller

1. **Performance**
   - Temps de réponse semantic search: < 500ms
   - Temps de réponse analytics: < 2s
   - Utilisation mémoire: < 512MB

2. **Coûts**
   - OpenAI API calls: ~$0.10/jour
   - Render compute: Selon plan
   - Supabase: Gratuit (plan actuel)

3. **Santé**
   - Database connections actives
   - Taux d'erreur API
   - Uptime services

### Alertes Recommandées

```yaml
# Sur Render Dashboard
Alerts:
  - CPU > 80% pendant 5min
  - Memory > 90%
  - Errors > 10/min
  - Response time > 5s
```

## 🔐 Sécurité

### Checklist

- ✅ `.env` dans `.gitignore`
- ✅ Secrets dans Render Environment
- ✅ RLS activé sur Supabase
- ✅ API keys avec restrictions
- ✅ HTTPS only
- ⚠️ Créer user roles séparés (production)

### Backup

```bash
# Backup Database (recommandé: quotidien)
# Via Supabase Dashboard ou:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Backup sur S3/Google Drive (automatique)
# Configure via Supabase Dashboard → Settings → Backups
```

## 🎯 Commandes Rapides

### Développement Local

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Éditer .env avec vos clés

# Tests
python test_semantic_search.py
python check_embedding_progress.py
python analyze_servitudes.py

# MCP Tools
python mcp_tools/semantic_search_mcp.py
python mcp_tools/property_analytics_mcp.py
```

### Render

```bash
# Deploy manuel
git push origin main

# Logs
render logs -s real-estate-embeddings

# Restart service
render services restart real-estate-embeddings

# Shell access
render shell real-estate-embeddings
```

## 🐛 Troubleshooting

### Erreur: "Module not found"

```bash
# Sur Render, vérifier requirements.txt
# Forcer rebuild:
render services restart --clear-cache
```

### Erreur: "Database connection failed"

```bash
# Vérifier DATABASE_URL
echo $DATABASE_URL

# Test connection
python -c "from supabase import create_client; client = create_client('$SUPABASE_URL', '$SUPABASE_KEY'); print(client.table('properties').select('id').limit(1).execute())"
```

### Erreur: "OpenAI rate limit"

```python
# Ajouter retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_embedding(text):
    return openai.embeddings.create(model="text-embedding-ada-002", input=text)
```

## 📝 Maintenance

### Tâches Régulières

**Quotidiennes:**
- Vérifier logs pour erreurs
- Monitoring coûts OpenAI

**Hebdomadaires:**
- Review performance metrics
- Check disk usage
- Backup database

**Mensuelles:**
- Update dependencies
- Review security
- Optimize queries lentes
- Cleanup old data

### Updates

```bash
# Update dependencies
pip list --outdated
pip install --upgrade <package>

# Update requirements.txt
pip freeze > requirements.txt

# Deploy
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

## 🎉 Checklist Déploiement

Avant de considérer le déploiement complet:

- [ ] Git repository initialisé
- [ ] `.gitignore` configuré
- [ ] Variables d'env sur Render
- [ ] render.yaml validé
- [ ] Tests locaux passent
- [ ] Documentation à jour
- [ ] MCP tools testés
- [ ] Backup configuré
- [ ] Monitoring activé
- [ ] git push effectué
- [ ] Déploiement Render vérifié
- [ ] Tests post-déploiement OK

## 💡 Optimisations Futures

### Performance

1. **Cache** 
   - Redis pour résultats fréquents
   - Cache embeddings OpenAI

2. **Database**
   - Index optimisés
   - Query optimization
   - Connection pooling

3. **API**
   - Rate limiting
   - CDN pour static
   - Compression responses

### Features

1. **Web Interface**
   - Dashboard interactif
   - Search UI
   - Admin panel

2. **Automations**
   - Cron jobs maintenance
   - Auto-reports
   - Alertes email

3. **Integrations**
   - Webhooks
   - API REST publique
   - Mobile app

---

**Ready to Deploy!** 🚀

Une fois le push Git fait, le système sera automatiquement déployé sur Render et les outils MCP seront disponibles via DATABASE_URL.

