#!/usr/bin/env python3
"""Test database connection and list properties"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')

print(f"\n🔍 SUPABASE_URL: {SUPABASE_URL[:50]}..." if SUPABASE_URL else "❌ SUPABASE_URL manquant")
print(f"🔑 SUPABASE_KEY: {'✅ Défini' if SUPABASE_KEY else '❌ Manquant'}\n")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Variables d'environnement manquantes dans .env")
    exit(1)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test connection
    props = supabase.table('properties').select('name, address').execute()
    
    print(f"✅ Connexion réussie!")
    print(f"📊 Propriétés trouvées: {len(props.data)}\n")
    
    if props.data:
        print("📋 LISTE DES PROPRIÉTÉS:")
        for i, p in enumerate(props.data, 1):
            print(f"   {i}. {p['name']} - {p.get('address', 'N/A')}")
    else:
        print("⚠️ Aucune propriété dans la base!")
        print("\n💡 Vérifier:")
        print("   1. La table 'properties' existe dans Supabase")
        print("   2. Les données ont été importées")
        print("   3. Les permissions RLS (service_role key)")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    print("\n💡 Vérifier le .env et les credentials Supabase")

