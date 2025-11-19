#!/usr/bin/env python3
"""Update .env with correct credentials"""

from pathlib import Path

env_content = """# Supabase Configuration
SUPABASE_URL=https://reqkkltmtaflbkchsmzb.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc

# Database Direct Connection
DATABASE_URL=postgresql://postgres.reqkkltmtaflbkchsmzb:Lau1sann2e5@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

# OpenAI (remplacer si nécessaire)
OPENAI_API_KEY=your_openai_api_key_here

# Azure OCR (si utilisé)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_azure_endpoint_here
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_azure_key_here
"""

# Backup existing .env
env_path = Path('.env')
if env_path.exists():
    backup_path = Path('.env.backup')
    backup_path.write_text(env_path.read_text(), encoding='utf-8')
    print("✅ Backup créé: .env.backup")

# Write new .env
env_path.write_text(env_content, encoding='utf-8')
print("✅ .env mis à jour avec:")
print("   - SUPABASE_URL")
print("   - SUPABASE_KEY (service_role)")
print("   - DATABASE_URL")
print("\n🔄 Redémarrer Claude Desktop pour appliquer les changements!")

