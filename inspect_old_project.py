"""
Inspect old Supabase project structure for migration planning
"""
from supabase import create_client

OLD_URL = "https://ugbfpxjpgtbxvcmimsap.supabase.co"
OLD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnYmZweGpwZ3RieHZjbWltc2FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjkyMjAzOCwiZXhwIjoyMDc4NDk4MDM4fQ.aTAMaBHhOqSb8mQsAOEeT7d4k21kmlLliM7moUNAkLY"

print("="*80)
print("  INSPECTION ANCIEN PROJET SUPABASE")
print("="*80)

try:
    old_supabase = create_client(OLD_URL, OLD_KEY)
    print("\n✅ Connexion établie")
    
    # Tables to check
    tables_to_check = [
        'documents', 'files', 'pdfs', 'doc',
        'document_chunks', 'chunks', 'embeddings', 'document_embeddings',
        'properties', 'tenants', 'leases', 'units'
    ]
    
    print("\n🔍 Recherche des tables...\n")
    
    found_tables = {}
    
    for table in tables_to_check:
        try:
            # Try to get schema and count
            result = old_supabase.table(table).select("*").limit(1).execute()
            
            if result.data and len(result.data) > 0:
                # Get column names
                columns = list(result.data[0].keys())
                
                # Get count
                count_result = old_supabase.table(table).select("*", count="exact").limit(1).execute()
                count = count_result.count
                
                found_tables[table] = {
                    'columns': columns,
                    'count': count,
                    'sample': result.data[0]
                }
                
                print(f"✅ Table: {table}")
                print(f"   Nombre d'enregistrements: {count:,}")
                print(f"   Colonnes ({len(columns)}): {', '.join(columns[:10])}")
                if len(columns) > 10:
                    print(f"              ... et {len(columns)-10} autres")
                print()
                
        except Exception as e:
            # Table doesn't exist or no access
            pass
    
    if not found_tables:
        print("❌ Aucune table trouvée")
        print("   Possibilités:")
        print("   - Les tables ont des noms différents")
        print("   - Le projet est vide")
        print("   - Problème de permissions")
    else:
        print(f"\n{'='*80}")
        print(f"  RÉSUMÉ")
        print(f"{'='*80}\n")
        
        print(f"📊 {len(found_tables)} tables trouvées:")
        for table_name, info in found_tables.items():
            print(f"   • {table_name}: {info['count']:,} enregistrements")
        
        # Analyze structure
        print(f"\n{'='*80}")
        print(f"  ANALYSE DÉTAILLÉE")
        print(f"{'='*80}\n")
        
        # Check for embeddings
        embeddings_tables = [t for t in found_tables.keys() if 'chunk' in t or 'embedding' in t]
        
        if embeddings_tables:
            print(f"🎯 Tables d'embeddings détectées: {', '.join(embeddings_tables)}\n")
            
            for emb_table in embeddings_tables:
                info = found_tables[emb_table]
                print(f"📄 {emb_table}:")
                print(f"   Structure:")
                
                # Check for key columns
                has_embedding = any('embedding' in col.lower() for col in info['columns'])
                has_text = any('text' in col.lower() or 'content' in col.lower() for col in info['columns'])
                has_doc_id = any('document' in col.lower() for col in info['columns'])
                
                print(f"   {'✅' if has_embedding else '❌'} Colonne embedding")
                print(f"   {'✅' if has_text else '❌'} Colonne texte/content")
                print(f"   {'✅' if has_doc_id else '❌'} Lien vers documents")
                
                # Show sample
                print(f"\n   Exemple d'enregistrement:")
                for key, value in list(info['sample'].items())[:5]:
                    if 'embedding' in key.lower():
                        print(f"      {key}: [vector {len(value) if isinstance(value, list) else '?'} dimensions]")
                    else:
                        str_value = str(value)[:50]
                        print(f"      {key}: {str_value}{'...' if len(str(value)) > 50 else ''}")
                print()
        
        # Check for documents
        doc_tables = [t for t in found_tables.keys() if 'doc' in t or 'file' in t or 'pdf' in t]
        
        if doc_tables:
            print(f"📁 Tables de documents détectées: {', '.join(doc_tables)}\n")
            
            for doc_table in doc_tables:
                info = found_tables[doc_table]
                print(f"📄 {doc_table}:")
                print(f"   Total: {info['count']:,} documents")
                
                # Check structure
                has_path = any('path' in col.lower() for col in info['columns'])
                has_name = any('name' in col.lower() for col in info['columns'])
                has_type = any('type' in col.lower() for col in info['columns'])
                
                print(f"   {'✅' if has_path else '❌'} Chemin fichier")
                print(f"   {'✅' if has_name else '❌'} Nom fichier")
                print(f"   {'✅' if has_type else '❌'} Type fichier")
                print()
        
        # Recommendations
        print(f"\n{'='*80}")
        print(f"  RECOMMANDATIONS MIGRATION")
        print(f"{'='*80}\n")
        
        total_chunks = sum(info['count'] for table, info in found_tables.items() if 'chunk' in table or 'embedding' in table)
        total_docs = sum(info['count'] for table, info in found_tables.items() if 'doc' in table or 'file' in table)
        
        if total_chunks > 0:
            print(f"✅ MIGRATION POSSIBLE")
            print(f"   Chunks à migrer: {total_chunks:,}")
            print(f"   Documents source: {total_docs:,}")
            print(f"\n   Temps estimé: {max(30, total_chunks//1000)} minutes")
            print(f"   Coût: 0 USD (réutilisation embeddings)")
            print(f"   Économie vs refaire: ~68 USD\n")
            
            print(f"📋 PROCHAINES ÉTAPES:")
            print(f"   1. Créer tables dans nouveau projet")
            print(f"   2. Migrer avec remapping des IDs")
            print(f"   3. Valider recherche sémantique")
            print(f"   4. Linker aux nouvelles données")
        else:
            print(f"⚠️  PAS D'EMBEDDINGS DÉTECTÉS")
            print(f"   Recommandation: Créer nouveaux embeddings (68 USD)")
            
except Exception as e:
    print(f"\n❌ Erreur: {str(e)}")
    print(f"   Vérifiez URL et service_role key")

print(f"\n✅ Inspection terminée\n")


