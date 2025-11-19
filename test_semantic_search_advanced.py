"""
Advanced semantic search with property/unit/tenant filtering
"""
from supabase import create_client
import openai

SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

OPENAI_API_KEY = "your_openai_api_key_here"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

print("="*80)
print("  RECHERCHE SÉMANTIQUE AVANCÉE - Avec Filtres")
print("="*80)

def semantic_search(query, property_name=None, unit_number=None, tenant_name=None, top_k=5):
    """
    Search with optional filters
    
    Args:
        query: Natural language question
        property_name: Filter by property (e.g., 'Gare 28', 'Pratifori 5-7')
        unit_number: Filter by unit (e.g., '3.05', '12')
        tenant_name: Filter by tenant
        top_k: Number of results
    """
    print(f"\n🔍 Question: {query}")
    
    if property_name:
        print(f"   📍 Propriété: {property_name}")
    if unit_number:
        print(f"   🏠 Unité: {unit_number}")
    if tenant_name:
        print(f"   👤 Locataire: {tenant_name}")
    
    # Generate embedding
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Search
    results = supabase.rpc('match_documents', {
        'query_embedding': query_embedding,
        'match_count': top_k * 3  # Get more, then filter
    }).execute()
    
    # Filter by metadata
    filtered_results = []
    for result in results.data:
        metadata = result.get('metadata') or {}
        
        # Apply filters
        if property_name and metadata.get('property_name') != property_name:
            continue
        if unit_number and metadata.get('unit_number') != unit_number:
            continue
        if tenant_name and tenant_name.lower() not in str(metadata.get('tenant_name', '')).lower():
            continue
        
        filtered_results.append(result)
        
        if len(filtered_results) >= top_k:
            break
    
    # Display
    print(f"\n📊 {len(filtered_results)} résultats:\n")
    
    for idx, match in enumerate(filtered_results, 1):
        metadata = match.get('metadata') or {}
        
        print(f"{idx}. Similarité: {match['similarity']:.3f}")
        print(f"   Propriété: {metadata.get('property_name', 'N/A')}")
        print(f"   Unité: {metadata.get('unit_number', 'N/A')}")
        print(f"   Locataire: {metadata.get('tenant_name', 'N/A')}")
        print(f"   Fichier: {metadata.get('file_name', 'N/A')}")
        print(f"   Texte: {match['chunk_text'][:150]}...")
        print()
    
    return filtered_results

# Examples
print("\n" + "="*80)
print("  EXEMPLES DE RECHERCHE")
print("="*80)

# Example 1: General search
print("\n📌 EXEMPLE 1: Recherche générale")
semantic_search("Quels locataires ont des animaux domestiques ?", top_k=3)

# Example 2: Property-specific
print("\n" + "="*80)
print("\n📌 EXEMPLE 2: Recherche par propriété")
semantic_search(
    "Quelles sont les clauses de résiliation ?",
    property_name="Pratifori 5-7",
    top_k=3
)

# Example 3: Unit-specific
print("\n" + "="*80)
print("\n📌 EXEMPLE 3: Recherche par unité")
semantic_search(
    "Quel est le loyer mensuel ?",
    property_name="Gare 28",
    unit_number="3.05",
    top_k=2
)

# Example 4: RAG - Generate answer
print("\n" + "="*80)
print("\n📌 EXEMPLE 4: RAG Complet (Question → Contexte → Réponse)")

def ask_with_rag(question, property_name=None):
    """Full RAG: Search + GPT-4 Answer"""
    
    # 1. Search
    results = semantic_search(question, property_name=property_name, top_k=5)
    
    if not results:
        return "Aucun document trouvé."
    
    # 2. Build context
    context = "\n\n".join([
        f"Document {i+1} (Propriété: {r.get('metadata', {}).get('property_name', 'N/A')}):\n{r['chunk_text']}"
        for i, r in enumerate(results)
    ])
    
    # 3. Generate answer
    print(f"\n💭 Génération réponse avec GPT-4...")
    
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """Tu es l'assistant du portefeuille immobilier. 
Réponds aux questions en te basant UNIQUEMENT sur les documents fournis.
Si l'information n'est pas dans les documents, dis-le clairement.
Cite la propriété et l'unité quand pertinent."""
            },
            {
                "role": "user",
                "content": f"""Documents disponibles:

{context}

Question: {question}

Réponds de manière précise et structurée."""
            }
        ],
        temperature=0.3
    )
    
    answer = completion.choices[0].message.content
    
    print(f"\n✨ Réponse:")
    print(f"{answer}\n")
    
    return answer

# Test RAG
ask_with_rag(
    "Quels sont les délais de préavis pour les appartements ?",
    property_name="Pratifori 5-7"
)

print("="*80)
print("\n✅ Tests terminés!")
print("\n💡 UTILISATION:")
print("""
from test_semantic_search_advanced import semantic_search, ask_with_rag

# Recherche simple
results = semantic_search("animaux autorisés ?")

# Recherche filtrée
results = semantic_search(
    "clauses de résiliation",
    property_name="Gare 28"
)

# RAG complet
answer = ask_with_rag(
    "Quel est le loyer mensuel ?",
    property_name="Pratifori 5-7"
)
""")


