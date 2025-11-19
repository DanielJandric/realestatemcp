"""
Analyze old Supabase project to understand structure before migration
"""

print("""
📊 QUESTIONNAIRE - ANCIEN PROJET EMBEDDINGS

Pour planifier la migration, j'ai besoin d'infos sur votre ancien projet:

1. STRUCTURE DES TABLES:
   
   a) Table documents:
      - Nom exact de la table? (ex: documents, files, pdfs)
      - Colonnes présentes? (ex: id, file_path, file_name, content, etc.)
      - Y a-t-il déjà des liens vers properties/tenants?
   
   b) Table chunks:
      - Nom exact? (ex: document_chunks, chunks, embeddings)
      - Colonnes? (ex: id, document_id, chunk_text, embedding, metadata)
      - Type d'embedding? (OpenAI 1536, autre?)
      - Index pgvector déjà créé?

2. DOCUMENTS ACTUELS:
   
   - Combien de documents? (vous dites "la plupart")
   - Combien de chunks total?
   - Taille totale des embeddings? (GB)
   - Les documents correspondent-ils aux 3'376 trouvés?
   - Ou c'est un autre ensemble?

3. MÉTADONNÉES:
   
   - Y a-t-il des métadonnées dans les chunks? (property_name, file_type, etc.)
   - Comment sont identifiés les documents? (par nom, par path?)
   - Y a-t-il déjà une catégorisation? (baux, assurances, etc.)

4. QUALITÉ:
   
   - Les embeddings fonctionnent bien?
   - Avez-vous déjà testé la recherche sémantique?
   - Y a-t-il des problèmes connus?

5. ACCÈS:
   
   - Project ID de l'ancien projet?
   - Avez-vous les credentials (service_role key)?
   - Région du projet? (même que le nouveau?)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RÉPONDEZ À CES QUESTIONS ET JE VOUS PROPOSERAI:

✅ Script de migration adapté
✅ Mapping des IDs automatique  
✅ Validation des données
✅ Plan B en cas de problème

""")

# Helper functions to connect to old project
OLD_PROJECT_URL = input("\n📝 Supabase URL ancien projet (ou ENTER pour skip): ").strip()
OLD_PROJECT_KEY = input("📝 Service role key ancien projet (ou ENTER pour skip): ").strip()

if OLD_PROJECT_URL and OLD_PROJECT_KEY:
    from supabase import create_client
    
    try:
        old_supabase = create_client(OLD_PROJECT_URL, OLD_PROJECT_KEY)
        
        print("\n🔍 Inspection automatique...\n")
        
        # Try to find tables
        tables_to_check = [
            'documents', 'files', 'pdfs',
            'document_chunks', 'chunks', 'embeddings',
            'document_embeddings'
        ]
        
        found_tables = {}
        
        for table in tables_to_check:
            try:
                result = old_supabase.table(table).select("*").limit(1).execute()
                if result.data:
                    found_tables[table] = result.data[0].keys()
                    print(f"✅ Table '{table}' trouvée")
                    print(f"   Colonnes: {', '.join(result.data[0].keys())}")
                    
                    # Count
                    count_result = old_supabase.table(table).select("*", count="exact").execute()
                    print(f"   Nombre: {count_result.count} enregistrements\n")
            except:
                pass
        
        if not found_tables:
            print("❌ Aucune table d'embeddings trouvée")
            print("   Vérifiez les credentials ou les noms de tables")
        else:
            print(f"\n✅ {len(found_tables)} tables pertinentes trouvées!")
            print("\n💡 Prêt à générer script de migration")
            
    except Exception as e:
        print(f"\n❌ Erreur connexion: {str(e)}")
        print("   Vérifiez URL et key")
else:
    print("\n⚠️  Mode manuel - répondez aux questions ci-dessus")

print("\n✅ Analyse terminée")


