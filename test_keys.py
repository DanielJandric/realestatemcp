#!/usr/bin/env python3
"""Test different Supabase keys"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

print(f"\n🔍 URL: {SUPABASE_URL}")
print(f"\n🔑 Clés disponibles:")
print(f"   SUPABASE_KEY: {'✅' if SUPABASE_KEY else '❌'} ({len(SUPABASE_KEY) if SUPABASE_KEY else 0} chars)")
print(f"   SUPABASE_SERVICE_KEY: {'✅' if SUPABASE_SERVICE_KEY else '❌'} ({len(SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else 0} chars)")

# Test avec la clé utilisée actuellement
current_key = SUPABASE_KEY or SUPABASE_SERVICE_KEY
print(f"\n🧪 Test avec clé actuelle...")

try:
    supabase = create_client(SUPABASE_URL, current_key)
    props = supabase.table('properties').select('name').execute()
    print(f"✅ Résultat: {len(props.data)} propriétés")
    if props.data:
        print(f"\n📋 Premières propriétés:")
        for p in props.data[:5]:
            print(f"   - {p['name']}")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Si on a une SERVICE_KEY différente, tester aussi
if SUPABASE_SERVICE_KEY and SUPABASE_SERVICE_KEY != SUPABASE_KEY:
    print(f"\n🧪 Test avec SERVICE_ROLE_KEY...")
    try:
        supabase2 = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        props2 = supabase2.table('properties').select('name').execute()
        print(f"✅ Résultat: {len(props2.data)} propriétés")
        if props2.data:
            print(f"\n📋 Premières propriétés:")
            for p in props2.data[:5]:
                print(f"   - {p['name']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

print(f"\n💡 Pour obtenir la bonne SERVICE_ROLE_KEY:")
print(f"   1. Supabase Dashboard → Settings → API")
print(f"   2. Copier 'service_role' key (pas 'anon')")
print(f"   3. Mettre à jour dans .env: SUPABASE_KEY=...")

