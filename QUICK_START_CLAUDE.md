# 🚀 Quick Start: Claude Desktop + Real Estate Intelligence

## ⚡ 3 Étapes pour Commencer

### 1️⃣ Installer les dépendances

```bash
cd C:\OneDriveExport
pip install supabase openai python-dotenv
```

### 2️⃣ Configurer Claude Desktop

**Fichier à éditer:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Contenu à ajouter:**

```json
{
  "mcpServers": {
    "real-estate": {
      "command": "python",
      "args": ["-m", "mcp_tools.server"],
      "env": {
        "SUPABASE_URL": "your_supabase_url_here",
        "SUPABASE_KEY": "your_supabase_service_role_key_here",
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

### 3️⃣ Redémarrer Claude Desktop

Fermer **complètement** Claude Desktop et le relancer.

---

## ✅ Test

Demander à Claude:

```
"Liste toutes mes propriétés avec leur taux d'occupation"
```

ou

```
"Trouve des informations sur les contrats de maintenance"
```

Claude utilisera automatiquement les outils MCP! 🎉

---

## 🛠️ 7 Outils Disponibles

| Outil | Description |
|-------|-------------|
| **semantic_search** | Recherche dans 31,605 chunks |
| **search_servitudes** | Servitudes et registre foncier |
| **get_property_dashboard** | Dashboard complet d'une propriété |
| **get_expiring_leases** | Baux à renouveler |
| **compare_properties** | Comparaison entre propriétés |
| **get_financial_summary** | Résumé financier global |
| **get_maintenance_summary** | Contrats de maintenance |

---

## 💡 Exemples de Questions

### Analyse de propriété
```
"Donne-moi un rapport complet sur Pratifori 5-7"
"Quel est le taux d'occupation de Gare 8-10?"
"Compare Pratifori 5-7 et St-Hubert 1"
```

### Recherche documentaire
```
"Trouve tous les contrats de maintenance pour le chauffage"
"Y a-t-il des incidents signalés ce mois-ci?"
"Quelles sont les clauses d'assurance importantes?"
```

### Planification
```
"Quels baux expirent dans les 3 prochains mois?"
"Quelle propriété est la plus rentable?"
"Combien je dépense en maintenance totale?"
```

### Juridique
```
"Quelles servitudes actives sur mes propriétés?"
"Y a-t-il des restrictions de construction?"
"Liste tous les droits de passage"
```

---

## 🐛 Problème?

### Test manuel du serveur:

```bash
cd C:\OneDriveExport
python mcp_tools/server.py
```

Devrait afficher:
```
🚀 Real Estate Intelligence MCP Server
✅ Connected to: https://reqkkltmtaflbkchsmzb.supabase.co
📊 Available tools: 7
✨ Server ready for Claude Desktop!
```

### Logs Claude Desktop:

- Windows: `%APPDATA%\Claude\Logs\`
- macOS: `~/Library/Logs/Claude/`

---

## 📚 Documentation Complète

- **CLAUDE_MCP_SETUP.md** - Setup détaillé et exemples
- **GUIDE_COMPLET_FINAL.md** - Guide utilisateur complet
- **FINAL_STATUS_BEFORE_DEPLOY.md** - État du système

---

**✨ C'est tout! Profitez de votre assistant immobilier intelligent!**

