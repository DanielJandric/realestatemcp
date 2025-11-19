# 🚀 Déploiement API sur Render

## 📋 Prérequis

- Compte Render.com
- Repository GitHub avec le code

## 🔧 Étapes de Déploiement

### 1. **Push sur GitHub**

```bash
git add .
git commit -m "API REST pour MCP Real Estate"
git push origin main
```

### 2. **Créer le Service sur Render**

1. Aller sur https://dashboard.render.com
2. Cliquer **"New +"** → **"Web Service"**
3. Connecter ton repo GitHub
4. Render détectera automatiquement `render.yaml`

### 3. **Configurer les Variables d'Environnement**

Dans Render Dashboard → Environment:

```
SUPABASE_URL=https://reqkkltmtaflbkchsmzb.supabase.co
SUPABASE_KEY=eyJhbGc... (ta clé service_role)
DATABASE_URL=postgresql://postgres.reqkkltmtaflbkchsmzb:Lau1sann2e5@...
OPENAI_API_KEY=sk-... (optionnel)
API_KEY=<généré automatiquement par Render>
```

### 4. **Déployer**

- Cliquer **"Create Web Service"**
- Attendre 2-3 minutes
- L'API sera disponible sur: `https://real-estate-api.onrender.com`

## 🔗 URLs Importantes

- **API Root**: `https://real-estate-api.onrender.com/`
- **Documentation**: `https://real-estate-api.onrender.com/docs`
- **Health Check**: `https://real-estate-api.onrender.com/health`
- **List Tools**: `https://real-estate-api.onrender.com/tools`

## 🔐 Utilisation

### Dans Claude Desktop (ou autre LLM)

**Option 1: MCP via HTTP** (nécessite un wrapper MCP)

**Option 2: API REST directe**

Exemple de configuration pour LLM qui supporte les API REST:

```json
{
  "customAPIs": [
    {
      "name": "Real Estate Intelligence",
      "baseUrl": "https://real-estate-api.onrender.com",
      "endpoints": [
        {
          "path": "/properties",
          "method": "GET",
          "description": "Liste des propriétés"
        },
        {
          "path": "/properties/{property}/dashboard",
          "method": "GET",
          "description": "Dashboard propriété"
        },
        {
          "path": "/call",
          "method": "POST",
          "description": "Appel outil MCP"
        }
      ]
    }
  ]
}
```

## 📡 Endpoints Principaux

### **GET /properties**
Liste toutes les propriétés

### **GET /properties/{name}/dashboard**
Dashboard complet d'une propriété

### **POST /call**
Appeler n'importe quel outil MCP
```json
{
  "tool": "get_property_dashboard",
  "arguments": {
    "property_name": "Pratifori"
  }
}
```

### **POST /sql**
Exécuter SQL (SELECT only)
```json
{
  "query": "SELECT * FROM v_revenue_summary LIMIT 10"
}
```

### **GET /analytics/etat-locatif**
État locatif complet

### **GET /analytics/anomalies**
Anomalies de loyers

### **GET /operations/expiring-leases**
Baux arrivant à échéance

## 🧪 Test Local (avant déploiement)

```bash
# Installer dépendances
pip install -r api/requirements.txt

# Lancer l'API
python -m uvicorn api.main:app --reload --port 8000

# Tester
curl http://localhost:8000/health
curl http://localhost:8000/tools
```

## 🔒 Sécurité

- ✅ API Key générée automatiquement
- ✅ Seules requêtes SELECT autorisées
- ✅ CORS configuré
- ✅ Rate limiting (via Render)

## 💰 Coûts

- **Plan Free**: OK pour démarrage (500h/mois)
- **Plan Starter ($7/mois)**: Recommandé pour production
- Auto-sleep après 15min inactivité (Free plan)

## 🚨 Important

Une fois déployé, **partage l'URL** avec ton équipe:
```
https://real-estate-api.onrender.com
```

Ils pourront configurer leur LLM pour s'y connecter!

