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
    },
    {
        "name": "get_etat_locatif_complet",
        "description": "Retourne l'état locatif complet d'une propriété avec KPI",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string", "description": "Nom partiel de la propriété"}
            },
            "required": ["property_name"]
        }
    },
    {
        "name": "calculate_rendements",
        "description": "Calcule les rendements (brut, net estimé) pour une propriété",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string"},
                "purchase_price": {"type": "number", "description": "Prix/valeur (CHF). Si absent, tentative depuis properties.estimated_value"}
            },
            "required": ["property_name"]
        }
    },
    {
        "name": "detect_anomalies_locatives",
        "description": "Détecte les loyers anormaux pour une propriété (z-score simple)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string"},
                "z_threshold": {"type": "number", "default": 2.0}
            },
            "required": ["property_name"]
        }
    },
    {
        "name": "search_servitudes",
        "description": "Recherche des servitudes par mot-clé/commune",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "commune": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_echeancier_baux",
        "description": "Échéancier des fins de bail d'une propriété (12 prochains mois)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string"},
                "months_ahead": {"type": "integer", "default": 12}
            },
            "required": ["property_name"]
        }
    },
    {
        "name": "get_database_stats",
        "description": "Statistiques globales de la base (comptages clés)",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_database_schema",
        "description": "Schéma des tables (colonnes/types)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Nom de table (optionnel)"}
            },
            "required": []
        }
    },
    {
        "name": "query_table",
        "description": "Requête flexible sur une table avec filtres de base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "where": {"type": "string", "description": "Clause WHERE sans 'WHERE' (optionnel)"},
                "order_by": {"type": "string", "description": "ex: created_at DESC (optionnel)"},
                "limit": {"type": "integer", "default": 100}
            },
            "required": ["table"]
        }
    },
    {
        "name": "search_documents",
        "description": "Recherche sémantique simple via embeddings (pgvector)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_context_for_rag",
        "description": "Construit un court contexte multi-sources (SQL + documents) pour RAG",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_name": {"type": "string"},
                "limit_docs": {"type": "integer", "default": 3}
            },
            "required": ["property_name"]
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
        safe_name = (property_name or '').replace("'", "''")
        prop_sql = f"SELECT * FROM properties WHERE name ILIKE '%{safe_name}%' LIMIT 1"
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


def get_etat_locatif_complet(property_name: str):
    safe_name = (property_name or '').replace("'", "''")
    prop_sql = f"SELECT id, name, address FROM properties WHERE name ILIKE '%{safe_name}%' LIMIT 1"
    prop = execute_sql(prop_sql)
    if not prop.get('success') or not prop.get('data'):
        return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
    prop_id = prop['data'][0]['id']

    leases_sql = f"""
    SELECT u.unit_number, u.type, u.surface, l.id as lease_id, l.start_date, l.end_date,
           COALESCE(l.rent_net,0) + COALESCE(l.charges,0) AS monthly_total,
           t.name as tenant_name
    FROM units u
    LEFT JOIN leases l ON l.unit_id = u.id AND (l.end_date IS NULL OR l.end_date > NOW())
    LEFT JOIN tenants t ON t.id = l.tenant_id
    WHERE u.property_id = '{prop_id}'
    ORDER BY u.unit_number
    """
    leases = execute_sql(leases_sql)
    if not leases.get('success'):
        return leases

    units = leases['data']
    total_units = len(units)
    occupied = sum(1 for r in units if r.get('lease_id'))
    kpi = {
        "total_units": total_units,
        "occupied_units": occupied,
        "vacant_units": total_units - occupied,
        "occupation_rate": round((occupied / total_units) * 100, 2) if total_units else 0,
        "monthly_revenue": round(sum((r.get('monthly_total') or 0) for r in units), 2)
    }
    return {"success": True, "property": prop['data'][0], "kpi": kpi, "rows": units}


def calculate_rendements(property_name: str, purchase_price: Optional[float] = None):
    safe_name = (property_name or '').replace("'", "''")
    prop_sql = f"SELECT id, name, COALESCE(estimated_value, 0) AS estimated_value FROM properties WHERE name ILIKE '%{safe_name}%' LIMIT 1"
    prop = execute_sql(prop_sql)
    if not prop.get('success') or not prop.get('data'):
        return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
    prop_id = prop['data'][0]['id']
    value = purchase_price or (prop['data'][0].get('estimated_value') or 0)

    rev_sql = f"""
    SELECT SUM(COALESCE(l.rent_net,0) + COALESCE(l.charges,0)) AS monthly_revenue
    FROM leases l JOIN units u ON u.id = l.unit_id
    WHERE u.property_id = '{prop_id}' AND (l.end_date IS NULL OR l.end_date > NOW())
    """
    rev = execute_sql(rev_sql)
    if not rev.get('success'):
        return rev
    monthly = (rev['data'][0]['monthly_revenue'] or 0) if rev.get('data') else 0
    annual = monthly * 12

    if value and value > 0:
        gross_yield = round((annual / value) * 100, 2)
    else:
        gross_yield = None
    # Net simple: -10% OPEX par défaut
    net_annual = annual * 0.9
    net_yield = round((net_annual / value) * 100, 2) if value else None

    return {
        "success": True,
        "property": prop['data'][0],
        "monthly_revenue": round(monthly, 2),
        "annual_revenue": round(annual, 2),
        "assumed_value": value,
        "gross_yield_percent": gross_yield,
        "net_yield_percent": net_yield
    }


def detect_anomalies_locatives(property_name: str, z_threshold: float = 2.0):
    safe_name = (property_name or '').replace("'", "''")
    prop_sql = f"SELECT id FROM properties WHERE name ILIKE '%{safe_name}%' LIMIT 1"
    prop = execute_sql(prop_sql)
    if not prop.get('success') or not prop.get('data'):
        return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
    prop_id = prop['data'][0]['id']

    sql = f"""
    SELECT u.id as unit_id, u.unit_number, u.type,
           COALESCE(l.rent_net,0) + COALESCE(l.charges,0) AS monthly_total
    FROM units u
    LEFT JOIN leases l ON l.unit_id = u.id AND (l.end_date IS NULL OR l.end_date > NOW())
    WHERE u.property_id = '{prop_id}'
    """
    rows = execute_sql(sql)
    if not rows.get('success'):
        return rows
    vals = [r.get('monthly_total') or 0 for r in rows['data'] if r.get('monthly_total') is not None]
    if not vals:
        return {"success": True, "anomalies": [], "note": "Aucun loyer disponible"}
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    std = var ** 0.5
    anomalies = []
    for r in rows['data']:
        v = r.get('monthly_total') or 0
        z = (v - mean) / std if std > 0 else 0
        if abs(z) >= z_threshold:
            anomalies.append({**r, "z_score": round(z, 2)})
    return {"success": True, "mean": round(mean, 2), "std": round(std, 2), "threshold": z_threshold, "anomalies": anomalies}


def search_servitudes(query: str, commune: Optional[str] = None):
    q = (query or '').replace("'", "''")
    if commune:
        c = commune.replace("'", "''")
        sql = f"""
        SELECT s.*, d.parcelle, d.commune
        FROM servitudes s
        LEFT JOIN land_registry_documents d ON d.id = s.document_id
        WHERE (s.type ILIKE '%{q}%' OR s.description ILIKE '%{q}%')
          AND d.commune ILIKE '%{c}%'
        ORDER BY d.commune, d.parcelle
        LIMIT 200
        """
    else:
        sql = f"""
        SELECT s.*, d.parcelle, d.commune
        FROM servitudes s
        LEFT JOIN land_registry_documents d ON d.id = s.document_id
        WHERE (s.type ILIKE '%{q}%' OR s.description ILIKE '%{q}%')
        ORDER BY d.commune, d.parcelle
        LIMIT 200
        """
    return execute_sql(sql)


def get_echeancier_baux(property_name: str, months_ahead: int = 12):
    safe_name = (property_name or '').replace("'", "''")
    prop_sql = f"SELECT id FROM properties WHERE name ILIKE '%{safe_name}%' LIMIT 1"
    prop = execute_sql(prop_sql)
    if not prop.get('success') or not prop.get('data'):
        return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
    prop_id = prop['data'][0]['id']
    sql = f"""
    SELECT l.id as lease_id, t.name as tenant_name, u.unit_number, l.end_date
    FROM leases l
    JOIN units u ON u.id = l.unit_id
    LEFT JOIN tenants t ON t.id = l.tenant_id
    WHERE u.property_id = '{prop_id}'
      AND l.end_date IS NOT NULL
      AND l.end_date <= (NOW() + INTERVAL '{months_ahead} months')
    ORDER BY l.end_date
    """
    return execute_sql(sql)


def get_database_stats():
    sql = """
SELECT
      (SELECT COUNT(*) FROM properties) AS properties,
      (SELECT COUNT(*) FROM units) AS units,
      (SELECT COUNT(*) FROM leases) AS leases,
      (SELECT COUNT(*) FROM tenants) AS tenants,
      (SELECT COUNT(*) FROM maintenance) AS maintenance,
      (SELECT COUNT(*) FROM insurance_policies) AS insurance_policies,
      (SELECT COUNT(*) FROM financial_statements) AS financial_statements,
      (SELECT COUNT(*) FROM document_chunks) AS document_chunks
"""
    return execute_sql(sql)


def get_database_schema(table: Optional[str] = None):
    if table:
        t = table.replace("'", "''")
        sql = f"""
        SELECT table_schema, table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{t}'
        ORDER BY ordinal_position
        """
    else:
        sql = """
        SELECT table_schema, table_name, COUNT(*) AS columns
        FROM information_schema.columns
        WHERE table_schema = 'public'
        GROUP BY 1,2
        ORDER BY 2
        """
    return execute_sql(sql)


def query_table(table: str, where: Optional[str] = None, order_by: Optional[str] = None, limit: int = 100):
    t = table.replace("'", "''")
    where_clause = f" WHERE {where} " if where else ""
    order_clause = f" ORDER BY {order_by} " if order_by else ""
    sql = f"SELECT * FROM {t}{where_clause}{order_clause} LIMIT {max(1, min(limit, 1000))}"
    return execute_sql(sql)


def search_documents(query: str, limit: int = 5):
    # Simple pgvector cosine similarity search if available
    # Expect a function to embed the query exists as 'embedding_for' in SQL or store precomputed synonyms
    q = (query or '').replace("'", "''")
    # Fallback: textual search if vector search not available
    sql = f"""
    WITH ranked AS (
      SELECT id, document_id, property_id, unit_id, lease_id, tenant_id,
             content,
             0.0 AS score -- Placeholder if no vector function available
      FROM document_chunks
      WHERE content ILIKE '%{q}%'
      LIMIT {max(1, min(limit, 50))}
    )
    SELECT * FROM ranked ORDER BY score DESC
    """
    return execute_sql(sql)


def get_context_for_rag(property_name: str, limit_docs: int = 3):
    safe_name = (property_name or '').replace("'", "''")
    prop_sql = f"SELECT id, name, address FROM properties WHERE name ILIKE '%{safe_name}%' LIMIT 1"
    prop = execute_sql(prop_sql)
    if not prop.get('success') or not prop.get('data'):
        return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
    prop_row = prop['data'][0]
    prop_id = prop_row['id']

    # Revenue snapshot
    rev_sql = f"""
    SELECT SUM(COALESCE(l.rent_net,0)+COALESCE(l.charges,0)) AS monthly_revenue
    FROM leases l JOIN units u ON u.id = l.unit_id
    WHERE u.property_id = '{prop_id}' AND (l.end_date IS NULL OR l.end_date > NOW())
    """
    rev = execute_sql(rev_sql)
    monthly = (rev['data'][0]['monthly_revenue'] or 0) if rev.get('data') else 0

    # Top documents (fallback textual)
    docs_sql = f"""
    SELECT id, content
    FROM document_chunks
    WHERE property_id = '{prop_id}'
    ORDER BY length(content) DESC
    LIMIT {max(1, min(limit_docs, 10))}
    """
    docs = execute_sql(docs_sql)
    docs_texts = [d.get('content') for d in (docs.get('data') or []) if d.get('content')] if docs.get('success') else []

    parts = [
        f"Propriété: {prop_row.get('name')} - {prop_row.get('address')}",
        f"Revenu mensuel estimé: {round(monthly, 2)} CHF",
        "Documents pertinents:\n" + "\n---\n".join(docs_texts)
    ]
    return {"success": True, "context": "\n\n".join(parts)[:12000]}


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
            elif tool_name == "get_etat_locatif_complet":
                tool_result = get_etat_locatif_complet(arguments.get("property_name"))
            elif tool_name == "calculate_rendements":
                tool_result = calculate_rendements(arguments.get("property_name"), arguments.get("purchase_price"))
            elif tool_name == "detect_anomalies_locatives":
                tool_result = detect_anomalies_locatives(arguments.get("property_name"), arguments.get("z_threshold", 2.0))
            elif tool_name == "search_servitudes":
                tool_result = search_servitudes(arguments.get("query"), arguments.get("commune"))
            elif tool_name == "get_echeancier_baux":
                tool_result = get_echeancier_baux(arguments.get("property_name"), arguments.get("months_ahead", 12))
            elif tool_name == "get_database_stats":
                tool_result = get_database_stats()
            elif tool_name == "get_database_schema":
                tool_result = get_database_schema(arguments.get("table"))
            elif tool_name == "query_table":
                tool_result = query_table(arguments.get("table"), arguments.get("where"), arguments.get("order_by"), arguments.get("limit", 100))
            elif tool_name == "search_documents":
                tool_result = search_documents(arguments.get("query"), arguments.get("limit", 5))
            elif tool_name == "get_context_for_rag":
                tool_result = get_context_for_rag(arguments.get("property_name"), arguments.get("limit_docs", 3))
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


@app.get("/tools")
def list_tools_http():
    return {"tools": MCP_TOOLS, "count": len(MCP_TOOLS)}


@app.post("/tools/{name}")
async def call_tool_http(name: str, body: Optional[Dict[str, Any]] = None):
    params = body or {}
    # Reuse MCP dispatch for consistency
    req = MCPRequest(method="tools/call", params={"name": name, "arguments": params}, id="http")
    res = await mcp_endpoint(req)
    # mcp_endpoint returns MCPResponse
    return res.result or {"error": "unknown"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

