# 🛡️ AMÉLIORATIONS CONNEXION INSTABLE

## 📋 Problème
Connexion instable qui plante souvent lors de l'embedding de 312 documents

## ✅ Solutions Implémentées

### 1. **Sauvegarde Automatique Toutes les 10 Entrées**
```python
# Dans embed_delta_only.py
if processed % 10 == 0:
    print(f"      💾 Sauvegarde auto ({processed} fichiers)...")
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
```

**Bénéfice**: En cas de crash, maximum 9 fichiers perdus (au lieu de tout perdre)

---

### 2. **Retry Logic avec Timeout**
```python
def generate_embedding(text, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000],
                timeout=30  # 30 second timeout
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                print(f"      ⚠️  Retry {attempt+1}/{max_retries} dans {wait_time}s...")
                time.sleep(wait_time)
```

**Bénéfice**: 
- Timeout de 30s pour éviter les blocages
- 3 tentatives avec backoff exponentiel (2s, 4s, 6s)
- Continue avec le fichier suivant en cas d'échec définitif

---

### 3. **Gestion des Interruptions (Ctrl+C)**
```python
def save_progress_and_exit(signum=None, frame=None):
    """Save progress on exit/crash"""
    if global_progress and PROGRESS_FILE_PATH:
        print("\n\n💾 Sauvegarde urgente avant arrêt...")
        with open(PROGRESS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(global_progress, f, indent=2, ensure_ascii=False)
        print("✅ Progression sauvée!")
    sys.exit(0)

signal.signal(signal.SIGINT, save_progress_and_exit)
signal.signal(signal.SIGTERM, save_progress_and_exit)
```

**Bénéfice**: Sauvegarde automatique même si vous faites Ctrl+C

---

### 4. **Try-Catch Robuste**
```python
try:
    print(f"\n📄 {file_path.name}")
    chunks, cost = process_file(file_path)
    # ... processing ...
    
except KeyboardInterrupt:
    # Save and re-raise
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    raise

except Exception as e:
    print(f"      ❌ ERREUR: {str(e)}")
    # Continue with next file
```

**Bénéfice**: Un fichier en erreur ne bloque pas tout le processus

---

### 5. **Auto-Restart Wrapper** (Optionnel)
```bash
python run_with_auto_restart.py
```

Relance automatiquement le script s'il plante complètement (jusqu'à 10 tentatives)

---

## 🔧 Scripts Disponibles

### Lancer l'embedding
```bash
cd C:\OneDriveExport
python embed_delta_only.py
```

### Monitoring temps réel (rafraîchissement 10s)
```bash
python watch_progress.py
```

### Monitoring ponctuel
```bash
python monitor_progress.py
```

### Avec auto-restart
```bash
python run_with_auto_restart.py
```

---

## 📊 Fonctionnalités du Monitoring

### `watch_progress.py` (temps réel)
- ✅ Progression en % avec barre visuelle
- ✅ Fichiers traités / restants
- ✅ Chunks créés
- ✅ Coût actuel et estimation totale
- ✅ Temps depuis dernière sauvegarde
- ✅ Temps restant estimé
- ✅ Rafraîchissement auto toutes les 10s

### `monitor_progress.py` (ponctuel)
- ✅ État global (fichiers, chunks, coût)
- ✅ Stats database (total chunks, % liés)
- ✅ Répartition par propriété
- ✅ Processus Python actifs
- ✅ Estimation restant (chunks, coût)
- ✅ Temps depuis dernière sauvegarde

---

## 🎯 Reprise Après Crash

Le script **reprend automatiquement** là où il s'était arrêté :

1. Lit `delta_embedding_progress.json`
2. Skip les fichiers déjà traités (par hash)
3. Continue avec les suivants

**Aucune action requise de votre part !**

---

## 💾 Fichier de Progression

**Location**: `C:\OneDriveExport\delta_embedding_progress.json`

**Structure**:
```json
{
  "processed": ["hash1", "hash2", ...],
  "total_chunks": 150,
  "total_cost": 0.45
}
```

**Sauvegardé**:
- Toutes les 10 entrées (pendant traitement)
- À la fin du script
- Sur Ctrl+C
- Sur signal SIGTERM

---

## 📈 Progression Actuelle

**Statut**: ✅ EN COURS
- Fichiers: **4/312** (1.3%)
- Prochaine sauvegarde: à 10 fichiers
- Estimation: ~1-2h pour tout traiter

---

## ⚙️ Paramètres Optimisés

```python
CHUNK_SIZE = 1000           # Taille chunk (mots)
CHUNK_OVERLAP = 200         # Overlap (mots)
SAVE_EVERY = 10             # Sauvegarde tous les X fichiers
MAX_RETRIES = 3             # Retry API
API_TIMEOUT = 30            # Timeout API (secondes)
BACKOFF = [2, 4, 6]         # Backoff entre retries (secondes)
```

---

## 🚨 En Cas de Problème

### Script bloqué ?
```bash
# Tuer tous les processus Python
Get-Process python | Stop-Process -Force

# Relancer
python embed_delta_only.py
```

### Vérifier l'état
```bash
python monitor_progress.py
```

### Voir les logs
```bash
# Dans le terminal où tourne le script
# Les erreurs s'affichent en temps réel
```

### Reset complet (dernier recours)
```bash
# Supprimer le fichier de progression
Remove-Item delta_embedding_progress.json

# Relancer (repart de zéro)
python embed_delta_only.py
```

---

## 📞 Support

Si le script plante systématiquement au même fichier :
1. Vérifier `embedding_log.txt` pour l'erreur exacte
2. Le fichier sera automatiquement skip après 3 tentatives
3. Le script continue avec les suivants

**Le système est conçu pour être résilient !** 💪


