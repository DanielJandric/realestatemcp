#!/usr/bin/env python3
"""
Real Estate MCP Server - SQL ONLY VERSION
All tools use execute_sql - NO Supabase client issues
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Any, Sequence
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

# Create MCP server
app = Server("real-estate-sql")


def execute_sql(query: str):
    """Execute SQL directly via psycopg2"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = [dict(row) for row in cur.fetchall()]
            conn.close()
            return {"success": True, "results": results, "count": len(results)}
        else:
            conn.commit()
            conn.close()
            return {"success": True, "message": "Query executed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_properties",
            description="Liste toutes les propriétés",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_property_dashboard",
            description="Dashboard complet d'une propriété",
            inputSchema={
                "type": "object",
                "properties": {"property_name": {"type": "string"}},
                "required": ["property_name"]
            }
        ),
        Tool(
            name="execute_sql",
            description="Requête SQL brute",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    try:
        if name == "list_properties":
            result = execute_sql("SELECT name, address FROM properties ORDER BY name")
        
        elif name == "get_property_dashboard":
            prop_name = arguments["property_name"]
            
            # Get property
            prop_sql = f"SELECT * FROM properties WHERE name ILIKE '%{prop_name}%' LIMIT 1"
            prop_res = execute_sql(prop_sql)
            
            if not prop_res['success'] or not prop_res['results']:
                result = {"success": False, "error": f"Propriété '{prop_name}' non trouvée"}
            else:
                prop = prop_res['results'][0]
                prop_id = prop['id']
                
                # Units
                units_sql = f"""
                SELECT u.*, 
                       COUNT(DISTINCT l.id) as lease_count,
                       SUM(CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN 1 ELSE 0 END) as active_leases
                FROM units u
                LEFT JOIN leases l ON l.unit_id = u.id
                WHERE u.property_id = '{prop_id}'
                GROUP BY u.id
                """
                units_res = execute_sql(units_sql)
                units = units_res.get('results', [])
                
                # Leases with tenants
                leases_sql = f"""
                SELECT l.*, t.name as tenant_name, u.unit_number
                FROM leases l
                JOIN units u ON l.unit_id = u.id
                LEFT JOIN tenants t ON l.tenant_id = t.id
                WHERE u.property_id = '{prop_id}'
                  AND (l.end_date IS NULL OR l.end_date > NOW())
                ORDER BY u.unit_number
                """
                leases_res = execute_sql(leases_sql)
                
                # Maintenance
                maint_sql = f"SELECT * FROM maintenance WHERE property_id = '{prop_id}'"
                maint_res = execute_sql(maint_sql)
                
                # Financials
                fin_sql = f"SELECT * FROM financial_statements WHERE property_id = '{prop_id}' LIMIT 1"
                fin_res = execute_sql(fin_sql)
                
                total_units = len(units)
                occupied = sum(1 for u in units if (u.get('active_leases') or 0) > 0)
                
                result = {
                    "success": True,
                    "property": prop,
                    "units": {
                        "total": total_units,
                        "occupied": occupied,
                        "vacant": total_units - occupied,
                        "occupation_rate": round(occupied / total_units * 100, 2) if total_units > 0 else 0,
                        "details": units
                    },
                    "leases": leases_res.get('results', []),
                    "maintenance": maint_res.get('results', []),
                    "financials": fin_res.get('results', [None])[0] if fin_res.get('success') else None
                }
        
        elif name == "execute_sql":
            query = arguments["query"]
            if not query.strip().upper().startswith('SELECT'):
                result = {"success": False, "error": "Only SELECT queries allowed"}
            else:
                result = execute_sql(query)
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False, default=str))]
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

