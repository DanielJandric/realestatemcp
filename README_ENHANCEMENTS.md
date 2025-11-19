# 🚀 MCP & Database - Améliorations Complètes

## 📋 Vue d'ensemble

Ce package contient des améliorations majeures pour votre système de gestion immobilière:

- **30+ nouveaux outils MCP** pour analytics avancés
- **Schéma de base de données renforcé** avec contraintes et vues matérialisées
- **Système de caching** pour optimiser les performances
- **Validation stricte des données** pour assurer la qualité
- **Détection de fraude et anomalies** automatisée
- **Rapports exécutifs** et benchmarking

## 📁 Fichiers créés

### Core Components

| Fichier | Description |
|---------|-------------|
| `schema_enhanced.sql` | Schéma DB avec contraintes CHECK, indexes composites, vues matérialisées, triggers |
| `mcp_server_enhanced.py` | Serveur MCP amélioré avec 30+ outils d'analyse |
| `mcp_cache.py` | Système de cache en mémoire avec TTL |
| `data_validator.py` | Validateurs pour tous les types d'entités |

### Scripts

| Fichier | Description |
|---------|-------------|
| `enhance_database.py` | Applique les améliorations SQL à Supabase |
| `test_mcp_enhanced.py` | Suite de tests pour tous les outils MCP |
| `test_database_constraints.py` | Vérifie que les contraintes fonctionnent |

## 🛠️ Installation & Configuration

### 1. Appliquer les améliorations à la base de données

**Option A: Via Supabase SQL Editor (Recommandé)**

1. Ouvrir https://reqkkltmtaflbkchsmzb.supabase.co
2. Aller dans SQL Editor
3. Copier le contenu de `schema_enhanced.sql`
4. Exécuter le script

**Option B: Via Script Python**

```bash
python enhance_database.py
```

⚠️ **Note**: Le script Python nécessite que la fonction `exec_sql` soit déjà disponible dans votre DB.

### 2. Tester le serveur MCP amélioré

```bash
# Tester tous les outils
python test_mcp_enhanced.py

# Tester les contraintes DB
python test_database_constraints.py
```

### 3. Utiliser le serveur MCP amélioré

**Remplacer l'ancien serveur:**

```bash
# Renommer l'ancien
mv mcp_server.py mcp_server_old.py

# Utiliser le nouveau
mv mcp_server_enhanced.py mcp_server.py
```

**Ou créer un nouveau serveur dans Claude Desktop:**

Modifier votre `claude_config.json`:

```json
{
  "mcpServers": {
    "RealEstateEnhanced": {
      "command": "python",
      "args": ["c:/OneDriveExport/mcp_server_enhanced.py"]
    }
  }
}
```

## 🎯 Nouveaux Outils MCP

### 📊 Analytics & Rapports

| Outil | Description |
|-------|-------------|
| `analyze_portfolio_performance()` | Analyse complète du portefeuille |
| `generate_financial_report()` | Rapport financier détaillé |
| `generate_executive_summary()` | Résumé exécutif global |
| `find_rent_anomalies(threshold)` | Détecte les loyers anormaux |
| `analyze_payment_patterns()` | Analyse des patterns de paiement |

### 🚨 Disputes & Incidents

| Outil | Description |
|-------|-------------|
| `get_active_disputes()` | Liste tous les litiges actifs |
| `analyze_incident_trends()` | Tendances des sinistres |

### 🎯 Prédiction & Optimisation

| Outil | Description |
|-------|-------------|
| `suggest_rent_optimization(unit_id)` | Suggère un loyer optimal |
| `predict_vacancy_risk()` | Prédit les risques de vacance |

### 🔍 Détection de Fraude

| Outil | Description |
|-------|-------------|
| `detect_fraud_patterns()` | Détecte patterns suspects |
| `find_duplicate_tenants()` | Trouve les doublons |

### 📈 Benchmarking

| Outil | Description |
|-------|-------------|
| `compare_property_performance(ids)` | Compare plusieurs propriétés |
| `benchmark_by_city(city)` | Benchmark par ville |

### 🔧 Maintenance

| Outil | Description |
|-------|-------------|
| `get_upcoming_maintenance()` | Contrats arrivant à échéance |
| `analyze_maintenance_costs()` | Analyse des coûts |

### 🛠️ Utilitaires

| Outil | Description |
|-------|-------------|
| `get_data_quality_report()` | Rapport qualité des données |
| `get_cache_stats()` | Statistiques du cache |
| `clear_cache(pattern)` | Vider le cache |

## 🗄️ Améliorations Base de Données

### Contraintes CHECK

✅ Validation automatique des données:
- Montants positifs (loyers, charges, dépôts)
- Dates logiques (end_date >= start_date)
- Emails valides
- Statuts valides (enum-like)
- Noms non vides

### Indexes Composites

⚡ Performance optimisée:
- `(property_id, status)` pour disputes/incidents
- `(tenant_id, status)` pour leases
- `(unit_id, status)` pour leases actifs
- Indexes trigram pour recherche textuelle

### Vues Matérialisées

📊 Rapports pré-calculés:
- `mv_portfolio_summary` - Résumé global du portefeuille
- `mv_property_metrics` - Métriques par propriété
- `mv_unit_type_analysis` - Analyse par type d'unité

**Rafraîchir les vues:**

```sql
SELECT refresh_all_materialized_views();
```

### Audit Trail

📝 Traçabilité complète:
- Table `audit_log` pour historique
- Triggers sur leases, disputes, incidents
- Stockage en JSONB des anciennes/nouvelles valeurs

### Fonctions PostgreSQL

🔧 Logique métier:
- `calculate_occupancy_rate(property_id)` - Taux d'occupation
- `get_rent_trend(property_id, months)` - Tendance des loyers
- `refresh_all_materialized_views()` - Rafraîchir toutes les vues

## 💾 Système de Cache

Le cache réduit les appels API Supabase:

```python
from mcp_cache import cached, invalidate_cache, get_cache_stats

@cached(ttl=300)  # Cache pendant 5 minutes
def my_expensive_query():
    # ...
    pass

# Vider le cache
invalidate_cache()  # Tout
invalidate_cache("property")  # Pattern spécifique

# Stats
stats = get_cache_stats()
```

## ✅ Validation des Données

Valide avant insertion:

```python
from data_validator import DataValidator

# Valider un tenant
result = DataValidator.validate_tenant({
    'name': 'Jean Dupont',
    'email': 'jean@example.com'
})

if result.valid:
    # Insérer
else:
    print(result.errors)

# Rapport qualité global
from data_validator import generate_data_quality_report
report = generate_data_quality_report(supabase)
```

## 📊 Exemples d'utilisation

### Via Python

```python
from mcp_server_enhanced import *

# Analyser le portfolio
portfolio = analyze_portfolio_performance()
print(portfolio)

# Trouver les anomalies de loyer (>30% écart)
anomalies = find_rent_anomalies(30.0)
print(anomalies)

# Optimiser le loyer d'une unité
suggestion = suggest_rent_optimization("unit-uuid-here")
print(suggestion)

# Détecter la fraude
fraud = detect_fraud_patterns()
print(fraud)

# Résumé exécutif
summary = generate_executive_summary()
print(summary)
```

### Via Claude Desktop

Une fois configuré dans Claude Desktop:

```
Génère-moi un résumé exécutif du portefeuille immobilier

Trouve les unités avec des loyers anormaux

Prédit les risques de vacance pour les 3 prochains mois

Compare la performance des propriétés à Fribourg et Sion

Détecte les patterns frauduleux dans les baux
```

## 🎨 Bonnes Pratiques

### Rafraîchir les vues matérialisées

Exécuter périodiquement (ex: quotidien via cron):

```sql
SELECT refresh_all_materialized_views();
```

### Vider le cache après modifications

Après mise à jour des données:

```python
from mcp_cache import invalidate_cache
invalidate_cache()
```

### Vérifier la qualité des données

Mensuellement:

```python
from data_validator import generate_data_quality_report
report = generate_data_quality_report(supabase)
# Corriger les issues trouvées
```

### Monitorer l'audit log

Vérifier régulièrement:

```sql
SELECT * FROM audit_log 
WHERE changed_at > NOW() - INTERVAL '7 days'
ORDER BY changed_at DESC;
```

## 🔧 Troubleshooting

### Les contraintes rejettent mes données

Les contraintes CHECK protègent l'intégrité. Vérifiez:
- Loyers/charges/dépôts >= 0
- Dates: end_date >= start_date
- Emails valides
- Statuts dans les valeurs permises

### Le cache ne fonctionne pas

Le cache est en mémoire et reset au redémarrage du serveur MCP. C'est normal.

### Les vues matérialisées sont vides

Exécutez: `SELECT refresh_all_materialized_views();`

### Performance lente

1. Vérifier que les indexes sont créés: `\d+ table_name`
2. Rafraîchir les vues matérialisées
3. Vérifier les stats du cache: `get_cache_stats()`

## 📈 Prochaines Étapes

✅ Intégration dans Claude Desktop
✅ Configuration des rapports automatiques
✅ Setup cron pour rafraîchir les vues
✅ Monitoring des anomalies
✅ Dashboard web (optionnel)

## 🆘 Support

Pour toute question:
1. Consulter les logs d'erreur
2. Vérifier la documentation Supabase
3. Tester avec les scripts de test fournis

---

**Créé le**: 2025-11-19  
**Version**: 1.0.0  
**Auteur**: AI Agent - Real Estate Analytics Enhancement
