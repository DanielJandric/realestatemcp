# 🤖 Configuration Claude Desktop avec MCP

## 📋 Vue d'ensemble

Votre système Real Estate Intelligence expose **7 outils sophistiqués** à Claude Desktop via le protocole MCP (Model Context Protocol). Claude pourra directement interroger votre base de données Supabase pour fournir des analyses en temps réel.

---

## 🛠️ Outils Disponibles pour Claude

### 1. **semantic_search** 🔍
Recherche intelligente dans 31,605 chunks de documents

**Capacités:**
- Recherche en langage naturel
- Filtrage par propriété
- Filtrage par catégorie de document
- Scoring de similarité

**Exemples de queries:**
```
"Trouve tous les contrats de maintenance pour le chauffage"
"Quelles sont les clauses d'assurance pour Pratifori 5-7?"
"Y a-t-il des incidents signalés à la Gare 8-10?"
```

### 2. **search_servitudes** 📜
Recherche dans le registre foncier et servitudes

**Capacités:**
- Recherche par propriété
- Filtrage par type de servitude
- Servitudes actives uniquement
- Détails complets (bénéficiaires, charges)

**Exemples:**
```
"Quelles servitudes actives sur Pratifori 5-7?"
"Liste tous les droits de passage"
"Y a-t-il des restrictions de construction sur mes propriétés?"
```

### 3. **get_property_dashboard** 🏢
Dashboard complet d'une propriété

**Données fournies:**
- Informations générales
- Unités et taux d'occupation
- Baux actifs et locataires
- Contrats de maintenance
- Polices d'assurance
- Servitudes actives
- Données financières

**Exemple:**
```
"Donne-moi le dashboard complet de Gare 8-10"
"Quel est le taux d'occupation de Pratifori 5-7?"
```

### 4. **get_expiring_leases** 📅
Baux arrivant à échéance

**Capacités:**
- Anticipation configurable (3, 6, 12 mois)
- Tri par date d'expiration
- Détails locataire et loyer
- Aide à la planification

**Exemples:**
```
"Quels baux expirent dans les 3 prochains mois?"
"Liste les renouvellements à prévoir cette année"
```

### 5. **compare_properties** ⚖️
Comparaison entre propriétés

**Métriques comparées:**
- Nombre d'unités
- Taux d'occupation
- Contrats de maintenance
- Servitudes actives
- Performance financière
- ROI

**Exemple:**
```
"Compare Pratifori 5-7 et Gare 8-10"
"Quelle propriété a le meilleur taux d'occupation?"
```

### 6. **get_financial_summary** 💰
Vue financière globale du portefeuille

**Données:**
- Revenus totaux
- Dépenses totales
- NOI (Net Operating Income)
- Par propriété et agrégé
- Taux de vacance

**Exemples:**
```
"Quel est mon NOI total?"
"Quelle propriété génère le plus de revenus?"
"Donne-moi un résumé financier complet"
```

### 7. **get_maintenance_summary** 🔧
Résumé contrats de maintenance

**Informations:**
- Tous les contrats actifs
- Coûts annuels totaux
- Par propriété
- Par prestataire
- Dates d'échéance

**Exemples:**
```
"Combien je dépense en maintenance totale?"
"Quels sont les contrats actifs pour Pratifori 5-7?"
"Liste tous les prestataires de maintenance"
```

---

## 🔧 Installation

### Étape 1: Localiser le fichier de config Claude

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### Étape 2: Ajouter la configuration MCP

Ouvrir `claude_desktop_config.json` et ajouter:

```json
{
  "mcpServers": {
    "real-estate-intelligence": {
      "command": "python",
      "args": ["-m", "mcp_tools.server"],
      "env": {
        "DATABASE_URL": "postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
        "SUPABASE_URL": "your_supabase_url_here",
        "SUPABASE_KEY": "your_supabase_service_role_key_here",
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

### Étape 3: Installer les dépendances Python

```bash
cd C:\OneDriveExport
pip install supabase openai python-dotenv
```

### Étape 4: Redémarrer Claude Desktop

Fermer complètement Claude Desktop et le relancer.

---

## ✅ Vérification

### Test local du serveur MCP

```bash
cd C:\OneDriveExport
python mcp_tools/server.py
```

Devrait afficher:
```
🚀 Real Estate Intelligence MCP Server
✅ Connected to: https://reqkkltmtaflbkchsmzb.supabase.co
📊 Available tools: 7
   - semantic_search: Recherche sémantique dans 31,605 chunks de documents
   - search_servitudes: Recherche de servitudes dans le registre foncier
   - get_property_dashboard: Dashboard complet d'une propriété
   - get_expiring_leases: Baux arrivant à échéance
   - compare_properties: Comparaison entre deux propriétés
   - get_financial_summary: Résumé financier global du portefeuille
   - get_maintenance_summary: Résumé des contrats de maintenance

✨ Server ready for Claude Desktop!
```

### Test dans Claude Desktop

Ouvrir une conversation et demander:

```
"Utilise l'outil semantic_search pour trouver des informations sur les assurances"
```

ou

```
"Donne-moi le dashboard de la propriété Pratifori 5-7"
```

Claude devrait automatiquement détecter et utiliser les outils MCP!

---

## 💡 Exemples d'utilisation avec Claude

### Analyse de propriété
```
User: "Je veux un rapport complet sur Pratifori 5-7"

Claude: *utilise get_property_dashboard("Pratifori 5-7")*
        *puis semantic_search pour documents pertinents*
        
        "Voici l'analyse complète de Pratifori 5-7:
        
        📊 Vue d'ensemble:
        - 45 unités (30 appartements, 15 parkings)
        - Taux d'occupation: 92.3%
        - 3 unités vacantes
        
        💰 Finances:
        - Revenus annuels: CHF 450,000
        - Dépenses: CHF 180,000
        - NOI: CHF 270,000
        
        🔧 Maintenance:
        - 7 contrats actifs
        - Coût annuel: CHF 45,000
        
        📜 Servitudes:
        - 2 servitudes actives
        - 1 droit de passage vers parcelle voisine
        - 1 restriction de construction (hauteur max 12m)
        
        [+ Détails complets]"
```

### Recherche documentaire
```
User: "Y a-t-il des problèmes signalés avec le chauffage?"

Claude: *utilise semantic_search("problèmes chauffage incidents")*
        
        "J'ai trouvé 3 incidents liés au chauffage:
        
        1. Gare 8-10 (12 Jan 2024): Panne chaudière
        2. Pratifori 5-7 (3 Mars 2024): Fuite radiateur appartement 204
        3. St-Hubert 1 (15 Avril 2024): Maintenance préventive
        
        [+ Détails et documents associés]"
```

### Planification stratégique
```
User: "Quels baux dois-je renouveler ce trimestre et quelle propriété est la plus rentable?"

Claude: *utilise get_expiring_leases(3)*
        *puis get_financial_summary()*
        *puis compare_properties pour top 2*
        
        "📅 Renouvellements Q1 2025:
        
        - 5 baux à renouveler:
          1. Pratifori 5-7, Apt 204 (31 Jan) - CHF 1,800/mois
          2. Gare 8-10, Apt 102 (15 Fév) - CHF 2,100/mois
          [...]
        
        💰 Propriété la plus rentable:
        
        St-Hubert 1 domine avec:
        - NOI: CHF 380,000/an
        - ROI: 8.2%
        - Taux d'occupation: 98%
        
        Comparé à Pratifori 5-7:
        - NOI: CHF 270,000/an
        - ROI: 6.5%
        - Taux d'occupation: 92.3%
        
        [+ Analyse détaillée et recommandations]"
```

### Recherche juridique
```
User: "Quelles propriétés ont des restrictions de construction?"

Claude: *utilise search_servitudes(servitude_type="restriction")*
        
        "🏗️ Restrictions de construction identifiées:
        
        1. Pratifori 5-7:
           - Hauteur max: 12m
           - Zone de protection du patrimoine
           - Base légale: Art. 123 Règlement communal
        
        2. Gare 8-10:
           - Interdiction extension côté nord
           - Servitude de non-aedificandi
           - Bénéficiaire: Parcelle n° 4567
        
        3. Pré d'Emoz:
           - Alignement obligatoire rue
           - Distance min 5m limites propriété
        
        [+ Documents registre foncier complets]"
```

---

## 🔐 Sécurité

### ✅ Bonnes pratiques

1. **Clés API dans config uniquement**
   - Ne jamais hardcoder dans le code
   - Ne jamais commiter dans Git

2. **Service Role Key Supabase**
   - Accès complet nécessaire pour MCP
   - Utiliser en local uniquement
   - Pas d'exposition publique

3. **OpenAI API Key**
   - Pour embeddings seulement
   - Monitoring des coûts
   - Rate limiting automatique

### 🔒 En production (futur)

Si vous voulez partager l'accès:

1. **Créer user roles séparés dans Supabase**
   ```sql
   CREATE ROLE mcp_readonly;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
   ```

2. **API Gateway avec authentification**
   - Ajouter JWT tokens
   - Rate limiting par user
   - Logging des accès

3. **Secrets management**
   - Utiliser service comme 1Password
   - Rotation automatique des clés
   - Audit trail

---

## 📊 Monitoring Usage

### Supabase Dashboard

Suivre:
- Nombre de queries
- Temps de réponse
- Bandwidth utilisé
- Connections actives

### OpenAI Usage

Surveiller:
- Coût par mois (embeddings queries)
- Nombre de recherches sémantiques
- Rate limit status

### Logs MCP

Claude Desktop logs:
```bash
# macOS
~/Library/Logs/Claude/

# Windows
%APPDATA%\Claude\Logs\
```

---

## 🚀 Capacités Avancées

### Multi-step Reasoning

Claude peut chaîner plusieurs outils:

```
User: "Analyse la santé financière de mon portefeuille et identifie les contrats de maintenance à renégocier"

Claude: 
1. *get_financial_summary()* → Identifie propriétés sous-performantes
2. *get_maintenance_summary()* → Récupère tous les contrats
3. *semantic_search("renouvellement maintenance")* → Trouve historique
4. *compare_properties()* → Benchmark coûts maintenance
5. Synthèse et recommandations
```

### Contextual Understanding

Claude comprend le contexte immobilier:

```
User: "Comment va Pratifori?"

Claude: *comprend que "Pratifori" = "Pratifori 5-7"*
        *utilise get_property_dashboard()*
        *répond de manière conversationnelle*
```

### Proactive Insights

```
User: "Que dois-je surveiller ce mois-ci?"

Claude: 
- *get_expiring_leases(1)* → Renouvellements urgents
- *get_maintenance_summary()* → Contrats à échéance
- *search_servitudes()* → Obligations légales
- *semantic_search("incident")* → Problèmes récents

→ Rapport proactif personnalisé
```

---

## 🐛 Troubleshooting

### Erreur: "MCP server not found"

**Solution:**
```bash
# Vérifier Python accessible
python --version

# Vérifier path du projet
cd C:\OneDriveExport
python mcp_tools/server.py

# Mettre le chemin absolu dans claude_desktop_config.json
"command": "C:\\Python311\\python.exe"
```

### Erreur: "Database connection failed"

**Vérifier:**
```python
# Test connexion
from supabase import create_client

supabase = create_client(
    'https://reqkkltmtaflbkchsmzb.supabase.co',
    'eyJhbGc...'
)

result = supabase.table('properties').select('id').limit(1).execute()
print(result.data)
```

### Erreur: "No tools available"

**Solution:**
1. Redémarrer Claude Desktop complètement
2. Vérifier `claude_desktop_config.json` syntaxe
3. Vérifier logs Claude Desktop

---

## 📚 Documentation Complète

### Fichiers de référence

- `GUIDE_COMPLET_FINAL.md` - Guide utilisateur complet
- `CAPACITES_FINALES_SYSTEME.md` - Vue d'ensemble système
- `FINAL_STATUS_BEFORE_DEPLOY.md` - État actuel
- `DEPLOY_GUIDE.md` - Déploiement (optionnel)

### Support

Pour questions ou problèmes:
1. Vérifier logs Claude Desktop
2. Tester connexions manuellement
3. Consulter documentation Supabase
4. Vérifier quotas OpenAI

---

## 🎉 C'est Prêt!

Votre système Real Estate Intelligence est maintenant **100% intégré à Claude Desktop**!

Claude peut:
- ✅ Rechercher dans 31,605 chunks de documents
- ✅ Analyser 8 propriétés en détail
- ✅ Comparer performances
- ✅ Identifier servitudes et restrictions
- ✅ Tracker baux et contrats
- ✅ Fournir insights financiers
- ✅ Répondre en langage naturel

**Profitez de votre assistant immobilier intelligent! 🏢🤖**

