#!/usr/bin/env python3
"""
Real Estate Intelligence API
Professional REST API for MCP Tools - Deployable on Render
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

# Import MCP tools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
import time

load_dotenv()

# Initialize
app = FastAPI(
    title="Real Estate Intelligence API",
    description="Professional MCP API for property management & analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Security
API_KEY = os.getenv('API_KEY', 'your-secret-api-key')


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Models
class ToolCallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


class SQLQueryRequest(BaseModel):
    query: str


# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.get("/")
def root():
    """API Root"""
    return {
        "service": "Real Estate Intelligence API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "tools_count": 22
    }


@app.get("/health")
def health():
    """Health check"""
    try:
        # Test DB connection
        result = supabase.rpc('exec_sql', {'sql': 'SELECT 1 as test'}).execute()
        db_status = "ok" if result.data else "error"
    except:
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status,
        "timestamp": time.time()
    }


@app.get("/tools")
def list_tools():
    """List all available tools"""
    return {
        "tools": [
            {
                "name": "list_properties",
                "description": "Liste toutes les propriétés",
                "category": "data"
            },
            {
                "name": "get_property_dashboard",
                "description": "Dashboard complet d'une propriété",
                "category": "analytics",
                "parameters": {"property_name": "string"}
            },
            {
                "name": "execute_sql",
                "description": "Exécute une requête SQL (SELECT only)",
                "category": "data",
                "parameters": {"query": "string"}
            },
            {
                "name": "get_etat_locatif_complet",
                "description": "État locatif avec KPI",
                "category": "analytics",
                "parameters": {"property_name": "string (optional)"}
            },
            {
                "name": "calculate_rendements",
                "description": "Calcule les rendements",
                "category": "finance",
                "parameters": {"property_name": "string"}
            },
            {
                "name": "detect_anomalies_locatives",
                "description": "Détecte anomalies de loyers",
                "category": "analytics"
            },
            {
                "name": "risk_assessment",
                "description": "Évaluation des risques",
                "category": "analytics",
                "parameters": {"property_name": "string"}
            },
            {
                "name": "get_expiring_leases",
                "description": "Baux arrivant à échéance",
                "category": "operations",
                "parameters": {"months": "integer"}
            },
            {
                "name": "fix_unit_types",
                "description": "Corrige les types d'unités",
                "category": "maintenance",
                "parameters": {"property_name": "string (optional)"}
            },
            {
                "name": "analyze_system",
                "description": "Auto-analyse du système",
                "category": "meta"
            }
        ]
    }


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.post("/call", dependencies=[])
def call_tool(request: ToolCallRequest):
    """
    Call any MCP tool
    
    Example:
    ```json
    {
        "tool": "get_property_dashboard",
        "arguments": {
            "property_name": "Pratifori"
        }
    }
    ```
    """
    try:
        # Import and call tool dynamically
        from mcp_tools.server_final import (
            list_properties,
            get_property_dashboard,
            execute_sql,
            fix_unit_types
        )
        
        tool_name = request.tool
        args = request.arguments
        
        if tool_name == "list_properties":
            result = list_properties()
        elif tool_name == "get_property_dashboard":
            result = get_property_dashboard(args.get("property_name"))
        elif tool_name == "execute_sql":
            result = execute_sql(args.get("query"))
        elif tool_name == "fix_unit_types":
            result = fix_unit_types(args.get("property_name"))
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sql", dependencies=[])
def execute_query(request: SQLQueryRequest):
    """
    Execute SQL query (SELECT only)
    
    Example:
    ```json
    {
        "query": "SELECT * FROM v_revenue_summary LIMIT 10"
    }
    ```
    """
    query = request.query.strip().upper()
    
    # Security: only SELECT
    if not query.startswith('SELECT') and not query.startswith('WITH'):
        raise HTTPException(status_code=403, detail="Only SELECT queries allowed")
    
    dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
    if any(kw in query for kw in dangerous):
        raise HTTPException(status_code=403, detail="Dangerous keywords detected")
    
    try:
        result = supabase.rpc('exec_sql', {'sql': request.query}).execute()
        return {
            "success": True,
            "rows": len(result.data) if result.data else 0,
            "data": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SHORTCUT ENDPOINTS (for common operations)
# ============================================================================

@app.get("/properties")
def get_properties():
    """Get all properties"""
    from mcp_tools.server_final import list_properties
    return list_properties()


@app.get("/properties/{property_name}/dashboard")
def get_dashboard(property_name: str):
    """Get property dashboard"""
    from mcp_tools.server_final import get_property_dashboard
    return get_property_dashboard(property_name)


@app.get("/analytics/etat-locatif")
def get_etat_locatif(property_name: Optional[str] = None):
    """Get état locatif"""
    try:
        sql = f"SELECT * FROM v_revenue_summary"
        if property_name:
            sql += f" WHERE property_name ILIKE '%{property_name}%'"
        
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/anomalies")
def get_anomalies():
    """Get rent anomalies"""
    try:
        result = supabase.rpc('exec_sql', {
            'sql': 'SELECT * FROM v_rent_anomalies WHERE status != \'Normal\' LIMIT 50'
        }).execute()
        return {"success": True, "anomalies": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/operations/expiring-leases")
def get_expiring(months: int = 6):
    """Get expiring leases"""
    try:
        result = supabase.rpc('exec_sql', {
            'sql': f'SELECT * FROM v_expiring_leases WHERE urgency IN (\'Urgent\', \'À surveiller\') LIMIT 100'
        }).execute()
        return {"success": True, "leases": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

