# 🤖 MCP Integration Guide

Guide pour utiliser les outils avancés avec MCP (Model Context Protocol)

## 📋 Vue d'Ensemble

MCP a accès direct à la database via `DATABASE_URL`. Les outils fournis exploitent cette connexion pour des analyses sophistiquées.

## 🛠️ Outils Disponibles

### 1. Semantic Search (`semantic_search_mcp.py`)

**Fonctions:**
- `semantic_search()` - Recherche sémantique avec filtres
- `search_servitudes()` - Recherche servitudes en langage naturel
- `multi_source_search()` - Recherche multi-source combinée

**Exemples d'utilisation:**

```python
# Recherche simple
results = semantic_search("contrats de maintenance coûteux")

# Recherche filtrée par propriété
results = semantic_search(
    "baux de location",
    property_name="Pratifori 5-7"
)

# Recherche par catégorie
results = semantic_search(
    "polices d'assurance",
    category="insurance"
)

# Recherche servitudes
servitudes = search_servitudes(
    "restrictions de construction",
    property_name="Banque 4",
    importance_level="critique"
)

# Multi-source (documents + servitudes + données structurées)
all_results = multi_source_search(
    "problèmes de maintenance",
    property_name="Pratifori 5-7"
)
```

### 2. Property Analytics (`property_analytics_mcp.py`)

**Fonctions:**
- `get_property_dashboard()` - Dashboard complet propriété
- `compare_properties()` - Comparaison multi-propriétés
- `get_expiring_leases()` - Baux expirant bientôt
- `get_servitudes_by_importance()` - Servitudes par niveau
- `get_maintenance_summary()` - Résumé contrats maintenance
- `get_financial_summary()` - Vue financière globale

**Exemples:**

```python
# Dashboard propriété
dashboard = get_property_dashboard("Pratifori 5-7")
print(f"Occupation: {dashboard['metrics']['occupation_rate']}%")
print(f"Revenue annuel: CHF {dashboard['metrics']['annual_revenue']}")
print(f"ROI: {dashboard['metrics']['roi_percent']}%")

# Comparaison
comparison = compare_properties()
for prop in comparison:
    print(f"{prop['name']}: {prop['occupation_rate']}% occupied")

# Baux expirant dans 6 mois
expiring = get_expiring_leases(months=6)
for lease in expiring:
    print(f"{lease['property']} - Unit {lease['unit']}: {lease['days_remaining']} jours")

# Vue financière globale
financial = get_financial_summary()
print(f"Revenue total: CHF {financial['revenue']['annual_total']}")
print(f"Coûts totaux: CHF {financial['costs']['total']}")
print(f"Revenu net: CHF {financial['net']['annual_income']}")
print(f"ROI portfolio: {financial['portfolio']['roi_percent']}%")
```

## 🔧 Configuration

### Variables d'Environnement Requises

```bash
# MCP fournit automatiquement:
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# À fournir:
SUPABASE_KEY=your_service_role_key
OPENAI_API_KEY=sk-proj-xxx
```

### Installation

```bash
# Dans le projet
pip install -r requirements.txt

# Les outils MCP sont dans /mcp_tools/
cd mcp_tools
```

## 📊 Cas d'Usage Avancés

### 1. Audit Complet Propriété

```python
# Combine analytics + semantic search
dashboard = get_property_dashboard("Banque 4")
docs = semantic_search("incidents problèmes", property_name="Banque 4")
servitudes = search_servitudes("restrictions", property_name="Banque 4")

report = {
    'metrics': dashboard['metrics'],
    'incidents_found': len(docs),
    'servitudes_critical': len([s for s in servitudes if s['importance'] == 'critique']),
    'recommendations': []
}

# Analyse automatique
if dashboard['metrics']['occupation_rate'] < 90:
    report['recommendations'].append("Taux d'occupation faible - vérifier causes")

if report['servitudes_critical'] > 0:
    report['recommendations'].append(f"{report['servitudes_critical']} servitudes critiques à vérifier")
```

### 2. Détection Anomalies

```python
# Compare actual vs expected
comparison = compare_properties()

for prop in comparison:
    # Occupation anormalement basse
    if prop['occupation_rate'] < 85:
        docs = semantic_search(f"résiliations départs", property_name=prop['name'])
        print(f"⚠️ {prop['name']}: occupation {prop['occupation_rate']}%")
        print(f"   Documents pertinents: {len(docs)}")
    
    # Revenue disproportionné
    avg_revenue_per_unit = prop['annual_rent'] / prop['units'] if prop['units'] > 0 else 0
    # Compare with portfolio average...
```

### 3. Analyse Prédictive

```python
# Prédire besoins maintenance
financial = get_financial_summary()
maintenance = get_maintenance_summary()

# Ratio maintenance/revenue
maintenance_ratio = (maintenance['total_annual_cost'] / 
                    financial['revenue']['annual_total'] * 100)

if maintenance_ratio > 15:  # Threshold
    print(f"⚠️ Ratio maintenance élevé: {maintenance_ratio:.1f}%")
    
    # Search for recurring issues
    results = semantic_search("pannes récurrentes problèmes fréquents")
    print(f"Problèmes identifiés: {len(results)}")
```

### 4. Génération Rapport Automatique

```python
def generate_monthly_report():
    """Génère rapport mensuel automatique"""
    
    report = {
        'date': datetime.now().isoformat(),
        'financial': get_financial_summary(),
        'expiring_leases': get_expiring_leases(months=3),
        'servitudes_critical': get_servitudes_by_importance()['critique'],
        'maintenance': get_maintenance_summary(),
        'property_comparison': compare_properties()
    }
    
    # Alertes automatiques
    alerts = []
    
    if len(report['expiring_leases']) > 5:
        alerts.append(f"{len(report['expiring_leases'])} baux expirent dans 3 mois")
    
    if report['servitudes_critical']['count'] > 0:
        alerts.append(f"{report['servitudes_critical']['count']} servitudes critiques")
    
    report['alerts'] = alerts
    
    return report
```

## 🎯 Requêtes Complexes pour MCP

### Exemple 1: "Analyse complète Pratifori 5-7"

```python
# MCP peut exécuter:
dashboard = get_property_dashboard("Pratifori 5-7")
documents = semantic_search("tous types documents", property_name="Pratifori 5-7", match_count=50)
servitudes = search_servitudes("toutes servitudes", property_name="Pratifori 5-7")
expiring = [l for l in get_expiring_leases(12) if l['property'] == 'Pratifori 5-7']

# Puis générer rapport synthétique
```

### Exemple 2: "Trouve propriétés avec problèmes"

```python
properties = compare_properties()
problems = []

for prop in properties:
    issues = []
    
    # Check occupation
    if prop['occupation_rate'] < 90:
        issues.append(f"Occupation {prop['occupation_rate']}%")
    
    # Check servitudes
    if prop['servitudes'] > 5:
        servitudes = search_servitudes("", property_name=prop['name'])
        critical = [s for s in servitudes if s['importance'] == 'critique']
        if critical:
            issues.append(f"{len(critical)} servitudes critiques")
    
    # Search for incidents
    incidents = semantic_search("incident sinistre problème", property_name=prop['name'], match_count=5)
    if len(incidents) > 3:
        issues.append(f"{len(incidents)} incidents récents")
    
    if issues:
        problems.append({
            'property': prop['name'],
            'issues': issues
        })

# Retourne liste propriétés avec problèmes
```

### Exemple 3: "Optimisation coûts maintenance"

```python
maintenance = get_maintenance_summary()

# Identify expensive contracts
expensive = []
for prop_name, data in maintenance['by_property'].items():
    for contract in data['contracts']:
        if contract['annual_cost'] > 10000:
            # Search for alternative providers in documents
            alternatives = semantic_search(
                f"fournisseur {contract['type']} prix",
                property_name=prop_name
            )
            
            expensive.append({
                'property': prop_name,
                'vendor': contract['vendor'],
                'cost': contract['annual_cost'],
                'potential_alternatives': len(alternatives)
            })

# Sort by cost
expensive.sort(key=lambda x: x['cost'], reverse=True)
```

## 🔐 Sécurité

### Bonnes Pratiques
- ✅ MCP a accès read-only par défaut (via DATABASE_URL)
- ✅ Toujours valider les inputs
- ✅ Limiter les résultats retournés (éviter surcharge)
- ✅ Logger les requêtes sensibles

### Rate Limiting
```python
# Pour OpenAI embeddings
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < 60 / calls_per_minute:
                time.sleep((60 / calls_per_minute) - elapsed)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

@rate_limit(calls_per_minute=50)
def semantic_search_with_limit(*args, **kwargs):
    return semantic_search(*args, **kwargs)
```

## 📝 Logs & Debugging

### Enable Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('mcp_tools')

# Dans les fonctions:
logger.info(f"Semantic search: {query}")
logger.debug(f"Results count: {len(results)}")
```

### Performance Monitoring
```python
import time

def timed(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

@timed
def slow_search(*args, **kwargs):
    return semantic_search(*args, **kwargs)
```

## 🚀 Déploiement

### Pour utiliser avec MCP:

1. **Assurer DATABASE_URL est disponible**
   ```bash
   export DATABASE_URL="postgresql://..."
   export SUPABASE_KEY="..."
   export OPENAI_API_KEY="..."
   ```

2. **Importer les outils dans MCP**
   ```python
   from mcp_tools.semantic_search_mcp import semantic_search, search_servitudes
   from mcp_tools.property_analytics_mcp import get_property_dashboard, get_financial_summary
   ```

3. **Utiliser via MCP**
   - MCP peut appeler directement les fonctions
   - Résultats retournés en JSON
   - Gestion d'erreurs automatique

## 💡 Tips & Tricks

### 1. Cache Results
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_property_dashboard(property_name: str):
    return get_property_dashboard(property_name)
```

### 2. Batch Operations
```python
def batch_search(queries: List[str], property_name: Optional[str] = None):
    results = {}
    for query in queries:
        results[query] = semantic_search(query, property_name=property_name)
        time.sleep(0.5)  # Rate limit
    return results
```

### 3. Error Handling
```python
def safe_search(query: str, **kwargs):
    try:
        return semantic_search(query, **kwargs)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {'error': str(e), 'query': query}
```

---

**Version:** 1.0  
**Last Updated:** 2025-11-19  
**Status:** ✅ Production Ready

