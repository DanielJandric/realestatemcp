#!/usr/bin/env python3
"""
Script de préparation pour commit Git
Vérifie que tout est prêt avant le push
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe"""
    if Path(filepath).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ MANQUANT: {description} ({filepath})")
        return False

def check_gitignore():
    """Vérifie le .gitignore"""
    if not Path('.gitignore').exists():
        print("❌ .gitignore manquant!")
        return False
    
    with open('.gitignore', 'r') as f:
        content = f.read()
    
    required = ['.env', 'OneDriveExport/', '*.pdf', '__pycache__']
    missing = [r for r in required if r not in content]
    
    if missing:
        print(f"⚠️  .gitignore incomplet. Manque: {missing}")
        return False
    
    print("✅ .gitignore configuré correctement")
    return True

def main():
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION PRÉ-COMMIT GIT")
    print("="*60 + "\n")
    
    checks = []
    
    # Documentation
    print("📚 DOCUMENTATION:")
    checks.append(check_file_exists('README.md', 'README principal'))
    checks.append(check_file_exists('CLAUDE_MCP_SETUP.md', 'Guide Claude MCP'))
    checks.append(check_file_exists('QUICK_START_CLAUDE.md', 'Quick Start Claude'))
    checks.append(check_file_exists('DEPLOY_GUIDE.md', 'Guide déploiement'))
    checks.append(check_file_exists('FINAL_STATUS_BEFORE_DEPLOY.md', 'État final'))
    
    # Configuration
    print("\n⚙️  CONFIGURATION:")
    checks.append(check_file_exists('.gitignore', '.gitignore'))
    checks.append(check_file_exists('requirements.txt', 'requirements.txt'))
    checks.append(check_file_exists('render.yaml', 'render.yaml'))
    checks.append(check_file_exists('env.example', 'env.example'))
    checks.append(check_file_exists('mcp_config_claude.json', 'Config MCP Claude'))
    
    # MCP Tools
    print("\n🤖 OUTILS MCP:")
    checks.append(check_file_exists('mcp_tools/server.py', 'Serveur MCP'))
    checks.append(check_file_exists('mcp_tools/semantic_search_mcp.py', 'Semantic Search'))
    checks.append(check_file_exists('mcp_tools/property_analytics_mcp.py', 'Property Analytics'))
    
    # Scripts principaux
    print("\n🐍 SCRIPTS PRINCIPAUX:")
    checks.append(check_file_exists('embed_delta_only.py', 'Embeddings delta'))
    checks.append(check_file_exists('link_all_chunks_complete.py', 'Linking chunks'))
    checks.append(check_file_exists('import_land_registry_with_ocr.py', 'Import registre foncier'))
    checks.append(check_file_exists('salvage_migrated_chunks_optimized.py', 'Salvage chunks'))
    
    # SQL
    print("\n🗄️  SCRIPTS SQL:")
    checks.append(check_file_exists('create_embeddings_tables.sql', 'Tables embeddings'))
    checks.append(check_file_exists('create_land_registry_tables.sql', 'Tables registre foncier'))
    
    # Vérifications spéciales
    print("\n🔐 SÉCURITÉ:")
    checks.append(check_gitignore())
    
    # Vérifier que .env n'existe pas (ou est dans gitignore)
    if Path('.env').exists():
        print("⚠️  ATTENTION: .env existe (mais devrait être ignoré par Git)")
    else:
        print("✅ Pas de fichier .env à la racine")
    
    # Résumé
    print("\n" + "="*60)
    total = len(checks)
    passed = sum(checks)
    failed = total - passed
    
    print(f"📊 RÉSUMÉ: {passed}/{total} vérifications passées")
    
    if failed > 0:
        print(f"❌ {failed} problème(s) détecté(s)")
        print("\n⚠️  Veuillez corriger les problèmes avant de commiter")
        return 1
    else:
        print("✅ Tous les fichiers sont prêts!")
        print("\n🚀 PRÊT POUR GIT COMMIT!")
        print("\nCommandes suggérées:")
        print("  git init")
        print("  git add .")
        print("  git commit -m 'feat: Real Estate Intelligence System v1.0'")
        print("  git remote add origin <your-repo-url>")
        print("  git push -u origin main")
        return 0

if __name__ == '__main__':
    sys.exit(main())

