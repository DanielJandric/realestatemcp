"""
Test semantic search on embedded documents
"""
from supabase import create_client
import openai

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

OPENAI_API_KEY = "your_openai_api_key_here"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

print("="*80)
print("  TEST RECHERCHE SÉMANTIQUE")
print("="*80)

def semantic_search(query, top_k=5):
    """Search for similar documents"""
    
    # Generate query embedding
    print(f"\n🔍 Question: {query}")
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Search using match_documents function
    result = supabase.rpc('match_documents', {
        'query_embedding': query_embedding,
        'match_count': top_k
    }).execute()
    
    if result.data:
        print(f"\n📊 {len(result.data)} résultats trouvés:\n")
        for idx, match in enumerate(result.data, 1):
            print(f"{idx}. Similarité: {match['similarity']:.3f}")
            print(f"   Texte: {match['chunk_text'][:200]}...")
            print()
    else:
        print("\n❌ Aucun résultat")

# Test queries
test_queries = [
    "Quels locataires peuvent avoir des animaux domestiques ?",
    "Quelle est la procédure en cas de fuite d'eau ?",
    "Quelles sont les clauses d'indexation des loyers ?",
    "Qui contacter pour la maintenance du chauffage ?",
    "Quels sont les préavis de résiliation ?"
]

print("\n🎯 TESTS AUTOMATIQUES\n")

for query in test_queries:
    semantic_search(query, top_k=3)
    print("="*80)

print("\n✅ Tests terminés!")
print("\n💡 Vous pouvez maintenant:")
print("   - Tester vos propres questions")
print("   - Implémenter le RAG complet")
print("   - Créer le chatbot locataire\n")


