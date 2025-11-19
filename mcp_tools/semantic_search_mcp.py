"""
MCP Tool: Advanced Semantic Search
Provides sophisticated search capabilities for MCP with database access
"""
import os
from supabase import create_client
import openai
from typing import Optional, List, Dict

# MCP will provide DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

supabase = create_client(DATABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY


def semantic_search(
    query: str,
    property_name: Optional[str] = None,
    category: Optional[str] = None,
    match_threshold: float = 0.7,
    match_count: int = 10
) -> List[Dict]:
    """
    Advanced semantic search with filters
    
    Args:
        query: Natural language search query
        property_name: Filter by property (e.g., 'Pratifori 5-7')
        category: Filter by category (e.g., 'lease', 'insurance', 'maintenance')
        match_threshold: Similarity threshold (0-1, default 0.7)
        match_count: Number of results to return
    
    Returns:
        List of matching chunks with metadata
    
    Examples:
        # Search all documents
        semantic_search("contrats de maintenance")
        
        # Search specific property
        semantic_search("baux de location", property_name="Pratifori 5-7")
        
        # Search by category
        semantic_search("polices d'assurance", category="insurance")
        
        # Combined filters
        semantic_search(
            "servitudes construction",
            property_name="Banque 4",
            category="land_registry"
        )
    """
    
    # Generate embedding
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Base search
    results = supabase.rpc('match_documents', {
        'query_embedding': query_embedding,
        'match_threshold': match_threshold,
        'match_count': match_count * 2  # Get more for filtering
    }).execute()
    
    # Post-filter
    filtered = []
    for chunk in results.data:
        meta = chunk.get('metadata', {})
        
        # Apply filters
        if property_name and meta.get('property_name') != property_name:
            continue
        if category and meta.get('category') != category:
            continue
        
        filtered.append({
            'chunk_text': chunk.get('chunk_text', '')[:500],  # Limit size
            'file_name': meta.get('file_name'),
            'property_name': meta.get('property_name'),
            'category': meta.get('category'),
            'similarity': chunk.get('similarity'),
            'document_id': chunk.get('document_id')
        })
        
        if len(filtered) >= match_count:
            break
    
    return filtered


def search_servitudes(
    query: str,
    property_name: Optional[str] = None,
    importance_level: Optional[str] = None
) -> List[Dict]:
    """
    Search servitudes with natural language
    
    Args:
        query: Search query (e.g., "restrictions construction")
        property_name: Filter by property
        importance_level: Filter by importance ('critique', 'importante', 'normale')
    
    Returns:
        List of matching servitudes
    """
    
    # Build SQL filter
    conditions = ["statut = 'active'"]
    
    if property_name:
        prop = supabase.table('properties').select('id').eq('name', property_name).execute()
        if prop.data:
            conditions.append(f"property_id = '{prop.data[0]['id']}'")
    
    if importance_level:
        conditions.append(f"importance_niveau = '{importance_level}'")
    
    where_clause = " AND ".join(conditions)
    
    # Search in servitudes table
    servitudes = supabase.table('servitudes')\
        .select('*, properties(name)')\
        .execute()
    
    # Filter by text relevance
    results = []
    query_lower = query.lower()
    
    for serv in servitudes.data:
        desc = (serv.get('description') or '').lower()
        type_serv = (serv.get('type_servitude') or '').lower()
        
        # Score based on relevance
        score = 0
        if query_lower in desc:
            score += 10
        if query_lower in type_serv:
            score += 5
        
        # Boost by importance
        if serv.get('importance_niveau') == 'critique':
            score += 3
        elif serv.get('importance_niveau') == 'importante':
            score += 2
        
        if score > 0:
            results.append({
                'score': score,
                'property': serv.get('properties', {}).get('name'),
                'type': serv.get('type_servitude'),
                'description': serv.get('description', '')[:200],
                'importance': serv.get('importance_niveau'),
                'impact_construction': serv.get('impact_constructibilite'),
                'impact_usage': serv.get('impact_usage'),
                'date_inscription': str(serv.get('date_inscription'))
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:10]


def multi_source_search(query: str, property_name: Optional[str] = None) -> Dict:
    """
    Search across multiple data sources
    
    Returns combined results from:
    - Document chunks (semantic)
    - Servitudes (structured)
    - Properties data (SQL)
    
    Args:
        query: Natural language query
        property_name: Optional property filter
    
    Returns:
        Dictionary with results from all sources
    """
    
    results = {
        'query': query,
        'property_filter': property_name,
        'documents': [],
        'servitudes': [],
        'properties': []
    }
    
    # 1. Semantic search on documents
    results['documents'] = semantic_search(
        query,
        property_name=property_name,
        match_count=5
    )
    
    # 2. Servitudes search
    results['servitudes'] = search_servitudes(
        query,
        property_name=property_name
    )[:5]
    
    # 3. Property data if relevant
    if property_name:
        prop_data = supabase.table('properties')\
            .select('*, units(count), leases(count), servitudes(count)')\
            .eq('name', property_name)\
            .execute()
        
        if prop_data.data:
            results['properties'] = prop_data.data
    
    return results


# Example usage for MCP
if __name__ == "__main__":
    # Test searches
    print("=== Test 1: Simple search ===")
    results = semantic_search("contrats de maintenance")
    print(f"Found {len(results)} results")
    
    print("\n=== Test 2: Property filter ===")
    results = semantic_search("baux", property_name="Pratifori 5-7")
    print(f"Found {len(results)} results for Pratifori")
    
    print("\n=== Test 3: Servitudes ===")
    results = search_servitudes("restriction construction")
    print(f"Found {len(results)} servitudes")
    
    print("\n=== Test 4: Multi-source ===")
    results = multi_source_search("problèmes maintenance", property_name="Banque 4")
    print(f"Documents: {len(results['documents'])}")
    print(f"Servitudes: {len(results['servitudes'])}")

