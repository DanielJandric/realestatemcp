"""
Extract tenant contacts from leases using semantic search + GPT-4
TODO 6: Extract contacts from PDFs
"""
from supabase import create_client
import openai
import json
import re

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

OPENAI_API_KEY = "your_openai_api_key_here"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

print("="*80)
print("  EXTRACTION CONTACTS LOCATAIRES (TODO 6)")
print("="*80)

# Get all tenants
print("\n📊 Récupération des locataires...")
tenants = supabase.table("tenants").select("*").execute().data
print(f"   {len(tenants)} locataires trouvés\n")

def extract_contacts_for_tenant(tenant_name):
    """Extract contact info for a specific tenant using semantic search"""
    
    # Search for tenant info in lease documents
    query = f"coordonnées contact téléphone email mobile urgence {tenant_name}"
    
    # Generate query embedding
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Search
    result = supabase.rpc('match_documents', {
        'query_embedding': query_embedding,
        'match_count': 3
    }).execute()
    
    if not result.data:
        return None
    
    # Combine relevant chunks
    context = "\n\n".join([chunk['chunk_text'] for chunk in result.data])
    
    # Use GPT-4 to extract structured contact info
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": """Tu es un assistant qui extrait des informations de contact depuis des documents.
Retourne un JSON avec ces champs (null si pas trouvé):
{
  "phone": "numéro principal",
  "mobile": "numéro mobile",
  "email": "email",
  "emergency_contact": "contact urgence avec numéro",
  "guarantor": "garant si mentionné"
}"""},
            {"role": "user", "content": f"Extrais les contacts pour: {tenant_name}\n\nDocuments:\n{context}"}
        ],
        temperature=0
    )
    
    try:
        # Parse JSON response
        contacts_json = completion.choices[0].message.content
        # Extract JSON from potential markdown
        if "```json" in contacts_json:
            contacts_json = contacts_json.split("```json")[1].split("```")[0].strip()
        elif "```" in contacts_json:
            contacts_json = contacts_json.split("```")[1].split("```")[0].strip()
        
        contacts = json.loads(contacts_json)
        return contacts
    except:
        return None

# Process all tenants
print(f"{'='*80}")
print(f"  EXTRACTION EN COURS")
print(f"{'='*80}\n")

updated = 0
skipped = 0

for tenant in tenants:
    tenant_name = tenant.get('name')
    tenant_id = tenant['id']
    
    # Skip if already has phone
    if tenant.get('phone'):
        skipped += 1
        continue
    
    print(f"📄 {tenant_name}")
    
    contacts = extract_contacts_for_tenant(tenant_name)
    
    if contacts:
        # Update tenant
        update_data = {}
        if contacts.get('phone'):
            update_data['phone'] = contacts['phone']
        if contacts.get('mobile'):
            update_data['mobile'] = contacts['mobile']
        if contacts.get('email'):
            update_data['email'] = contacts['email']
        if contacts.get('emergency_contact'):
            update_data['emergency_contact'] = contacts['emergency_contact']
        if contacts.get('guarantor'):
            update_data['guarantor'] = contacts['guarantor']
        
        if update_data:
            try:
                supabase.table("tenants").update(update_data).eq("id", tenant_id).execute()
                print(f"   ✅ {len(update_data)} champs mis à jour")
                updated += 1
            except Exception as e:
                print(f"   ❌ Erreur: {str(e)}")
        else:
            print(f"   ⚠️  Aucune donnée trouvée")
    else:
        print(f"   ⚠️  Pas de résultats")

print(f"\n{'='*80}")
print(f"  RÉSULTATS")
print(f"{'='*80}\n")

print(f"✅ Locataires mis à jour: {updated}")
print(f"⏭️  Locataires skippés: {skipped}")
print(f"📊 Total: {len(tenants)}")

print(f"\n✅ TODO 6 terminé!\n")


