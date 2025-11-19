#!/usr/bin/env python3
"""
MCP Server for Real Estate Intelligence System
Exposes advanced tools to Claude Desktop via Model Context Protocol
"""

import os
import json
from pathlib import Path
from typing import Any, Optional
from supabase import create_client
import openai
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize clients
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY


# ============================================================================
# SEMANTIC SEARCH TOOLS
# ============================================================================

def semantic_search(
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    property_filter: Optional[str] = None,
    category_filter: Optional[str] = None
) -> dict[str, Any]:
    """
    🔍 Recherche sémantique intelligente dans tous les documents
    
    Args:
        query: Question ou recherche en langage naturel
        limit: Nombre de résultats à retourner (défaut: 10)
        threshold: Seuil de similarité 0-1 (défaut: 0.7)
        property_filter: Filtrer par propriété (ex: "Pratifori 5-7")
        category_filter: Filtrer par catégorie (ex: "bail", "assurance")
    
    Returns:
        dict avec résultats: chunks, métadonnées, scores de similarité
    
    Example:
        semantic_search("contrats maintenance chauffage", limit=5)
        semantic_search("assurances", property_filter="Gare 8-10")
    """
    try:
        # Generate embedding for query
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = response.data[0].embedding
        
        # Build filter metadata
        filter_metadata = {}
        if property_filter:
            filter_metadata['property_name'] = property_filter
        if category_filter:
            filter_metadata['category'] = category_filter
        
        # Execute search via RPC function
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': limit,
                'filter_metadata': filter_metadata if filter_metadata else None
            }
        ).execute()
        
        return {
            'success': True,
            'query': query,
            'results_count': len(result.data),
            'results': result.data
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query
        }


def search_servitudes(
    query: Optional[str] = None,
    property_name: Optional[str] = None,
    servitude_type: Optional[str] = None,
    active_only: bool = True
) -> dict[str, Any]:
    """
    📜 Recherche de servitudes dans le registre foncier
    
    Args:
        query: Recherche texte libre dans descriptions
        property_name: Filtrer par propriété
        servitude_type: Type de servitude (ex: "droit_de_passage")
        active_only: Seulement les servitudes actives (défaut: True)
    
    Returns:
        dict avec servitudes trouvées et détails
    
    Example:
        search_servitudes(property_name="Pratifori 5-7")
        search_servitudes(servitude_type="droit_de_passage")
    """
    try:
        query_builder = supabase.table('servitudes').select(
            '*, properties(name), land_registry_documents(file_name)'
        )
        
        if active_only:
            query_builder = query_builder.eq('is_active', True)
        
        if property_name:
            # Join with properties table
            query_builder = query_builder.eq('properties.name', property_name)
        
        if servitude_type:
            query_builder = query_builder.eq('servitude_type', servitude_type)
        
        if query:
            query_builder = query_builder.ilike('description', f'%{query}%')
        
        result = query_builder.execute()
        
        return {
            'success': True,
            'servitudes_count': len(result.data),
            'servitudes': result.data
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# PROPERTY ANALYTICS TOOLS
# ============================================================================

def get_property_dashboard(property_name: str) -> dict[str, Any]:
    """
    🏢 Dashboard complet d'une propriété
    
    Args:
        property_name: Nom de la propriété (ex: "Pratifori 5-7")
    
    Returns:
        dict avec:
        - Infos générales
        - Unités et occupation
        - Finances
        - Contrats maintenance
        - Assurances
        - Servitudes actives
    
    Example:
        get_property_dashboard("Pratifori 5-7")
    """
    try:
        # Get property
        prop = supabase.table('properties').select('*').eq('name', property_name).execute()
        if not prop.data:
            return {'success': False, 'error': f'Propriété "{property_name}" non trouvée'}
        
        property_data = prop.data[0]
        property_id = property_data['id']
        
        # Get units
        units = supabase.table('units').select(
            '*, leases(*, tenants(name))'
        ).eq('property_id', property_id).execute()
        
        # Get maintenance contracts
        maintenance = supabase.table('maintenance').select('*').eq(
            'property_id', property_id
        ).execute()
        
        # Get insurance
        insurance = supabase.table('insurance_policies').select('*').eq(
            'property_id', property_id
        ).execute()
        
        # Get servitudes
        servitudes = supabase.table('servitudes').select('*').eq(
            'property_id', property_id
        ).eq('is_active', True).execute()
        
        # Get financial statements
        financials = supabase.table('financial_statements').select('*').eq(
            'property_id', property_id
        ).execute()
        
        # Calculate occupation
        total_units = len(units.data)
        occupied_units = sum(1 for u in units.data if u.get('leases'))
        occupation_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        return {
            'success': True,
            'property': property_data,
            'units': {
                'total': total_units,
                'occupied': occupied_units,
                'vacant': total_units - occupied_units,
                'occupation_rate': round(occupation_rate, 2),
                'details': units.data
            },
            'maintenance_contracts': {
                'total': len(maintenance.data),
                'contracts': maintenance.data
            },
            'insurance': insurance.data,
            'servitudes': {
                'total_active': len(servitudes.data),
                'details': servitudes.data
            },
            'financials': financials.data[0] if financials.data else None
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'property_name': property_name
        }


def get_expiring_leases(months_ahead: int = 6) -> dict[str, Any]:
    """
    📅 Baux arrivant à échéance dans les N prochains mois
    
    Args:
        months_ahead: Nombre de mois à anticiper (défaut: 6)
    
    Returns:
        dict avec baux expirants, triés par date
    
    Example:
        get_expiring_leases(3)  # 3 mois
    """
    try:
        result = supabase.rpc(
            'get_expiring_leases',
            {'months': months_ahead}
        ).execute()
        
        # If RPC doesn't exist, use direct query
        if not result.data:
            # Fallback query
            from datetime import datetime, timedelta
            future_date = datetime.now() + timedelta(days=30 * months_ahead)
            
            result = supabase.table('leases').select(
                '*, units(unit_number, properties(name)), tenants(name)'
            ).lte('end_date', future_date.isoformat()).gte(
                'end_date', datetime.now().isoformat()
            ).order('end_date').execute()
        
        return {
            'success': True,
            'months_ahead': months_ahead,
            'expiring_count': len(result.data),
            'leases': result.data
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def compare_properties(property1: str, property2: str) -> dict[str, Any]:
    """
    ⚖️ Comparaison détaillée entre deux propriétés
    
    Args:
        property1: Nom de la première propriété
        property2: Nom de la deuxième propriété
    
    Returns:
        dict avec comparaison côte-à-côte
    
    Example:
        compare_properties("Pratifori 5-7", "Gare 8-10")
    """
    try:
        dash1 = get_property_dashboard(property1)
        dash2 = get_property_dashboard(property2)
        
        if not dash1['success'] or not dash2['success']:
            return {
                'success': False,
                'error': 'Une ou les deux propriétés non trouvées'
            }
        
        return {
            'success': True,
            'comparison': {
                property1: {
                    'units': dash1['units']['total'],
                    'occupation_rate': dash1['units']['occupation_rate'],
                    'maintenance_contracts': dash1['maintenance_contracts']['total'],
                    'active_servitudes': dash1['servitudes']['total_active'],
                    'financials': dash1['financials']
                },
                property2: {
                    'units': dash2['units']['total'],
                    'occupation_rate': dash2['units']['occupation_rate'],
                    'maintenance_contracts': dash2['maintenance_contracts']['total'],
                    'active_servitudes': dash2['servitudes']['total_active'],
                    'financials': dash2['financials']
                }
            },
            'full_details': {
                property1: dash1,
                property2: dash2
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_financial_summary() -> dict[str, Any]:
    """
    💰 Résumé financier global de tous les immeubles
    
    Returns:
        dict avec agrégations financières par propriété et totaux
    
    Example:
        get_financial_summary()
    """
    try:
        # Get all properties with financials
        properties = supabase.table('properties').select(
            '*, financial_statements(*)'
        ).execute()
        
        total_revenue = 0
        total_expenses = 0
        total_noi = 0
        
        properties_summary = []
        
        for prop in properties.data:
            fs = prop.get('financial_statements', [])
            if fs:
                fs = fs[0]  # Latest financial statement
                revenue = fs.get('total_revenue', 0) or 0
                expenses = fs.get('total_expenses', 0) or 0
                noi = fs.get('noi', 0) or 0
                
                total_revenue += revenue
                total_expenses += expenses
                total_noi += noi
                
                properties_summary.append({
                    'property': prop['name'],
                    'revenue': revenue,
                    'expenses': expenses,
                    'noi': noi,
                    'vacancy_rate': fs.get('vacancy_rate', 0)
                })
        
        return {
            'success': True,
            'portfolio_summary': {
                'total_revenue': round(total_revenue, 2),
                'total_expenses': round(total_expenses, 2),
                'total_noi': round(total_noi, 2),
                'properties_count': len(properties.data)
            },
            'by_property': properties_summary
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_maintenance_summary() -> dict[str, Any]:
    """
    🔧 Résumé des contrats de maintenance
    
    Returns:
        dict avec tous les contrats, coûts annuels, par propriété
    
    Example:
        get_maintenance_summary()
    """
    try:
        contracts = supabase.table('maintenance').select(
            '*, properties(name)'
        ).execute()
        
        total_annual_cost = sum(
            c.get('annual_cost', 0) or 0 for c in contracts.data
        )
        
        by_property = {}
        for contract in contracts.data:
            prop_name = contract.get('properties', {}).get('name', 'Unknown')
            if prop_name not in by_property:
                by_property[prop_name] = {
                    'contracts': [],
                    'total_cost': 0
                }
            by_property[prop_name]['contracts'].append(contract)
            by_property[prop_name]['total_cost'] += contract.get('annual_cost', 0) or 0
        
        return {
            'success': True,
            'total_contracts': len(contracts.data),
            'total_annual_cost': round(total_annual_cost, 2),
            'by_property': by_property,
            'all_contracts': contracts.data
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# MCP SERVER INTERFACE
# ============================================================================

TOOLS = [
    {
        'name': 'semantic_search',
        'description': 'Recherche sémantique dans 31,605 chunks de documents',
        'function': semantic_search
    },
    {
        'name': 'search_servitudes',
        'description': 'Recherche de servitudes dans le registre foncier',
        'function': search_servitudes
    },
    {
        'name': 'get_property_dashboard',
        'description': 'Dashboard complet d\'une propriété',
        'function': get_property_dashboard
    },
    {
        'name': 'get_expiring_leases',
        'description': 'Baux arrivant à échéance',
        'function': get_expiring_leases
    },
    {
        'name': 'compare_properties',
        'description': 'Comparaison entre deux propriétés',
        'function': compare_properties
    },
    {
        'name': 'get_financial_summary',
        'description': 'Résumé financier global du portefeuille',
        'function': get_financial_summary
    },
    {
        'name': 'get_maintenance_summary',
        'description': 'Résumé des contrats de maintenance',
        'function': get_maintenance_summary
    }
]


def main():
    """MCP Server entry point"""
    print("🚀 Real Estate Intelligence MCP Server")
    print(f"✅ Connected to: {SUPABASE_URL}")
    print(f"📊 Available tools: {len(TOOLS)}")
    for tool in TOOLS:
        print(f"   - {tool['name']}: {tool['description']}")
    print("\n✨ Server ready for Claude Desktop!")


if __name__ == '__main__':
    main()

