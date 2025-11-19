#!/usr/bin/env python3
"""
MCP Server over HTTP for LLM Manus and other MCP clients
Implements the Model Context Protocol via HTTP instead of stdio
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client

load_dotenv()

app = FastAPI(title="Real Estate MCP Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))


# MCP Protocol Models
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


# MCP Tool definitions
MCP_TOOLS = [
    {
        "name": "list_properties",
        "description": "Liste toutes les propriétés",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_property_dashboard",
        "description": "Dashboard complet d'une propriété",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "Nom de la propriété"}
            },
            "required": ["property_name"]
        }
    },
    {
        "name": "execute_sql",
        "description": "Exécute une requête SQL (SELECT only)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Requête SQL"}
            },
            "required": ["query"]
        }
    }
]


def execute_sql(query: str):
    """Execute SQL query"""
    query_upper = query.strip().upper()
    if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
        return {"success": False, "error": "Only SELECT queries allowed"}
    
    try:
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        return {"success": True, "data": result.data, "count": len(result.data) if result.data else 0}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_properties():
    """List all properties"""
    result = execute_sql("SELECT name, address FROM properties ORDER BY name")
    if result.get('success'):
        return {"success": True, "properties": result['data'], "count": result['count']}
    return result


def get_property_dashboard(property_name: str):
    """Get property dashboard"""
    try:
        # Get property
        prop_sql = f"SELECT * FROM properties WHERE name ILIKE '%{property_name}%' LIMIT 1"
        prop_result = execute_sql(prop_sql)
        
        if not prop_result.get('success') or not prop_result.get('data'):
            return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
        
        prop = prop_result['data'][0]
        prop_id = prop['id']
        
        # Get units
        units_sql = f"""
        SELECT u.*, COUNT(l.id) as lease_count
        FROM units u
        LEFT JOIN leases l ON l.unit_id = u.id AND (l.end_date IS NULL OR l.end_date > NOW())
        WHERE u.property_id = '{prop_id}'
        GROUP BY u.id
        """
        units_result = execute_sql(units_sql)
        
        # Get leases
        leases_sql = f"""
        SELECT l.*, t.name as tenant_name, u.unit_number
        FROM leases l
        JOIN units u ON l.unit_id = u.id
        LEFT JOIN tenants t ON l.tenant_id = t.id
        WHERE u.property_id = '{prop_id}' AND (l.end_date IS NULL OR l.end_date > NOW())
        """
        leases_result = execute_sql(leases_sql)
        
        units = units_result.get('data', [])
        total_units = len(units)
        occupied = sum(1 for u in units if (u.get('lease_count') or 0) > 0)
        
        return {
            "success": True,
            "property": prop,
            "units": {
                "total": total_units,
                "occupied": occupied,
                "vacant": total_units - occupied,
                "occupation_rate": round(occupied / total_units * 100, 2) if total_units > 0 else 0,
                "details": units
            },
            "leases": leases_result.get('data', [])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """
    MCP Protocol endpoint
    Handles all MCP method calls
    """
    
    method = request.method
    params = request.params or {}
    
    try:
        # Handle MCP methods
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "real-estate-mcp",
                    "version": "1.0.0"
                }
            }
        
        elif method == "tools/list":
            result = {"tools": MCP_TOOLS}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "list_properties":
                tool_result = list_properties()
            elif tool_name == "get_property_dashboard":
                tool_result = get_property_dashboard(arguments.get("property_name"))
            elif tool_name == "execute_sql":
                tool_result = execute_sql(arguments.get("query"))
            else:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": str(tool_result)
                    }
                ]
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        return MCPResponse(
            jsonrpc="2.0",
            result=result,
            id=request.id
        )
    
    except Exception as e:
        return MCPResponse(
            jsonrpc="2.0",
            error={"code": -32603, "message": str(e)},
            id=request.id
        )


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Real Estate MCP Server (HTTP)",
        "protocol": "MCP 2024-11-05",
        "endpoint": "/mcp",
        "tools_count": len(MCP_TOOLS)
    }


@app.get("/health")
def health():
    """Health check"""
    try:
        result = execute_sql("SELECT 1 as test")
        db_status = "ok" if result.get('success') else "error"
    except:
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

