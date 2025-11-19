#!/usr/bin/env python3
"""
MCP Server for Real Estate Intelligence - Proper stdio implementation
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import openai

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize clients
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY


def semantic_search(query: str, limit: int = 10):
    """Semantic search in documents"""
    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = response.data[0].embedding
        
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.7,
                'match_count': limit
            }
        ).execute()
        
        return {
            'success': True,
            'results': result.data
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def list_properties():
    """List all properties"""
    try:
        props = supabase.table('properties').select('name, id, address').execute()
        return {
            'success': True,
            'properties': props.data,
            'count': len(props.data)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_property_dashboard(property_name: str):
    """Get complete property dashboard"""
    try:
        # Try exact match first
        prop = supabase.table('properties').select('*').eq('name', property_name).execute()
        
        # If not found, try case-insensitive search
        if not prop.data:
            prop = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
        
        if not prop.data:
            # List available properties
            all_props = supabase.table('properties').select('name').execute()
            available = [p['name'] for p in all_props.data]
            return {
                'success': False, 
                'error': f'Property "{property_name}" not found',
                'available_properties': available
            }
        
        property_data = prop.data[0]
        property_id = property_data['id']
        
        units = supabase.table('units').select('*, leases(*, tenants(name))').eq('property_id', property_id).execute()
        maintenance = supabase.table('maintenance').select('*').eq('property_id', property_id).execute()
        servitudes = supabase.table('servitudes').select('*').eq('property_id', property_id).eq('is_active', True).execute()
        
        total_units = len(units.data)
        occupied_units = sum(1 for u in units.data if u.get('leases'))
        occupation_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        return {
            'success': True,
            'property': property_data,
            'units_total': total_units,
            'units_occupied': occupied_units,
            'units_vacant': total_units - occupied_units,
            'occupation_rate': round(occupation_rate, 2),
            'maintenance_contracts': len(maintenance.data),
            'active_servitudes': len(servitudes.data),
            'units_details': units.data[:10]  # Limit to 10 for readability
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# MCP Protocol handler
def handle_mcp_request(request):
    """Handle MCP JSON-RPC request"""
    method = request.get('method')
    params = request.get('params', {})
    request_id = request.get('id', 0)
    
    if method == 'initialize':
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'protocolVersion': '2024-11-05',
                'serverInfo': {
                    'name': 'real-estate-intelligence',
                    'version': '1.0.0'
                },
                'capabilities': {
                    'tools': {}
                }
            }
        }
    
    elif method == 'tools/list':
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'tools': [
                    {
                        'name': 'list_properties',
                        'description': 'List all available properties',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {}
                        }
                    },
                    {
                        'name': 'semantic_search',
                        'description': 'Search documents by meaning',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'query': {'type': 'string', 'description': 'Search query'},
                                'limit': {'type': 'integer', 'description': 'Number of results', 'default': 10}
                            },
                            'required': ['query']
                        }
                    },
                    {
                        'name': 'get_property_dashboard',
                        'description': 'Get complete property information. Use list_properties first to see available names.',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'property_name': {'type': 'string', 'description': 'Exact name of the property (case-sensitive)'}
                            },
                            'required': ['property_name']
                        }
                    }
                ]
            }
        }
    
    elif method == 'tools/call':
        tool_name = params.get('name')
        tool_args = params.get('arguments', {})
        
        if tool_name == 'list_properties':
            result = list_properties()
        elif tool_name == 'semantic_search':
            result = semantic_search(**tool_args)
        elif tool_name == 'get_property_dashboard':
            result = get_property_dashboard(**tool_args)
        else:
            result = {'success': False, 'error': f'Unknown tool: {tool_name}'}
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        }
    
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'error': {
            'code': -32601,
            'message': f'Method not found: {method}'
        }
    }


def main():
    """Main stdio loop"""
    # Send ready signal
    sys.stderr.write("MCP Server ready\n")
    sys.stderr.flush()
    
    for line in sys.stdin:
        request_id = 0
        try:
            request = json.loads(line)
            request_id = request.get('id', 0)
            response = handle_mcp_request(request)
            
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()


if __name__ == '__main__':
    main()

