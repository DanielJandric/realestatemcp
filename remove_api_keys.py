#!/usr/bin/env python3
"""
Script pour remplacer les clés API par des placeholders
"""

import re
from pathlib import Path

# Pattern pour détecter les clés OpenAI
OPENAI_PATTERN = r'sk-proj-[A-Za-z0-9_-]+'

# Fichiers à nettoyer
files_to_clean = [
    'import_land_registry_with_ocr.py',
    'test_semantic_search.py',
    'test_semantic_search_advanced.py',
    'QUICK_START.md',
    'embed_delta_only.py',
    'extract_tenant_contacts.py',
    'import_and_embed_all_documents.py',
    'test_single_file.py',
    'validate_setup.py',
    'embed_delta_clean.py',
]

def clean_file(filepath):
    """Remplace les clés API dans un fichier"""
    path = Path(filepath)
    if not path.exists():
        print(f"⏭️  Fichier non trouvé: {filepath}")
        return False
    
    content = path.read_text(encoding='utf-8')
    original = content
    
    # Remplacer les clés OpenAI
    content = re.sub(OPENAI_PATTERN, 'your_openai_api_key_here', content)
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f"✅ Nettoyé: {filepath}")
        return True
    else:
        print(f"⏭️  Aucune clé trouvée: {filepath}")
        return False

def main():
    print("\n🧹 NETTOYAGE DES CLÉS API...\n")
    
    cleaned = 0
    for file in files_to_clean:
        if clean_file(file):
            cleaned += 1
    
    print(f"\n✅ {cleaned} fichiers nettoyés")
    print("🔒 Les clés API ont été remplacées par des placeholders")
    print("\n💡 Vos clés réelles restent dans .env (ignoré par Git)")

if __name__ == '__main__':
    main()

