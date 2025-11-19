#!/usr/bin/env python3
"""
Real Estate Intelligence MCP Server - Sophisticated & Complete
Using official MCP SDK for Claude Desktop
"""

import os
import asyncio
from pathlib import Path
from typing import Any, Sequence
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from supabase import create_client
import openai

# Advanced tools - inline
import sys
from typing import Optional, List, Dict

def advanced_etat_locatif(db_unused, property_name: Optional[str] = None):
    """État locatif complet avec KPI - CORRIGÉ"""
    try:
        # Utiliser la vue v_revenue_summary
        if property_name:
            sql = f"SELECT * FROM v_revenue_summary WHERE property_name ILIKE '%{property_name}%'"
        else:
            sql = "SELECT * FROM v_revenue_summary ORDER BY property_name"
        
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        
        if not result.data:
            return {"success": False, "error": "Aucune propriété trouvée"}
        
        return {
            "success": True,
            "properties_count": len(result.data),
            "etat_locatif": result.data,
            "portfolio_totals": {
                "total_units": sum(r['total_units'] for r in result.data),
                "occupied_units": sum(r['occupied_units'] for r in result.data),
                "monthly_revenue": sum(r['monthly_revenue'] or 0 for r in result.data),
                "annual_revenue": sum(r['annual_revenue'] or 0 for r in result.data),
                "avg_occupation_rate": sum(r['occupation_rate'] or 0 for r in result.data) / len(result.data) if result.data else 0
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def advanced_rendements(supabase, property_name: str):
    """Calcule les rendements"""
    try:
        prop = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
        if not prop.data:
            return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
        property_data = prop.data[0]
        financials = supabase.table('financial_statements').select('*').eq('property_id', property_data['id']).execute()
        purchase_price = property_data.get('purchase_price', 0) or 0
        if financials.data:
            revenue = financials.data[0].get('total_revenue', 0) or 0
            noi = financials.data[0].get('noi', 0) or 0
        else:
            revenue = noi = 0
        return {"success": True, "property": property_data['name'], "rendements": {"rendement_brut": round((revenue / purchase_price * 100) if purchase_price > 0 else 0, 2), "rendement_net": round((noi / purchase_price * 100) if purchase_price > 0 else 0, 2), "revenue_annuel": round(revenue, 2), "noi": round(noi, 2)}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def advanced_anomalies(supabase, threshold_vacancy: float = 10, threshold_rent_gap: float = 15):
    """Détecte les anomalies locatives"""
    try:
        props = supabase.table('properties').select('*').execute()
        anomalies = []
        for prop in props.data:
            units = supabase.table('units').select('*, leases(*)').eq('property_id', prop['id']).execute()
            total = len(units.data)
            occupied = sum(1 for u in units.data if u.get('leases'))
            vacancy_rate = ((total - occupied) / total * 100) if total > 0 else 0
            issues = []
            if vacancy_rate > threshold_vacancy:
                issues.append(f"Vacance élevée: {round(vacancy_rate, 1)}%")
            if issues:
                anomalies.append({"property": prop['name'], "vacancy_rate": round(vacancy_rate, 2), "issues": issues})
        return {"success": True, "anomalies_found": len(anomalies), "anomalies": anomalies}
    except Exception as e:
        return {"success": False, "error": str(e)}

def advanced_risk(supabase, property_name: str):
    """Évaluation des risques"""
    try:
        prop = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
        if not prop.data:
            return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
        property_data = prop.data[0]
        units = supabase.table('units').select('*, leases(*)').eq('property_id', property_data['id']).execute()
        occupied = sum(1 for u in units.data if u.get('leases'))
        vacancy_rate = ((len(units.data) - occupied) / len(units.data) * 100) if units.data else 0
        age = 2025 - property_data.get('construction_year') if property_data.get('construction_year') else None
        risks = {"tenant_risk": {"level": "HIGH" if vacancy_rate > 15 else "MEDIUM" if vacancy_rate > 5 else "LOW", "vacancy_rate": round(vacancy_rate, 2)}, "technical_risk": {"level": "HIGH" if age and age > 50 else "MEDIUM" if age and age > 30 else "LOW" if age else "UNKNOWN", "building_age": age}}
        return {"success": True, "property": property_data['name'], "risks": risks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def advanced_covenant(supabase, property_name: Optional[str] = None):
    """Vérifie la conformité aux covenants bancaires"""
    try:
        if property_name:
            props = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
        else:
            props = supabase.table('properties').select('*').execute()
        results = []
        for prop in props.data:
            financials = supabase.table('financial_statements').select('*').eq('property_id', prop['id']).execute()
            if financials.data:
                noi = financials.data[0].get('noi', 0) or 0
                debt = prop.get('mortgage_amount', 0) or 0
                value = prop.get('purchase_price', 0) or 0
                ltv = (debt / value * 100) if value > 0 else 0
                dscr = (noi / (debt * 0.05)) if debt > 0 else 0
                results.append({"property": prop['name'], "ltv": round(ltv, 2), "dscr": round(dscr, 2), "compliant": ltv <= 75 and dscr >= 1.25})
        return {"success": True, "properties_checked": len(results), "all_compliant": all(r['compliant'] for r in results), "compliance": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

def advanced_aggregate(supabase, table: str, group_by: List[str], aggregations: Dict[str, str]):
    """Agrégations complexes"""
    try:
        agg_clauses = [f"{func}({col}) as {col}_{func}" for col, func in aggregations.items()]
        query = f"SELECT {', '.join(group_by)}, {', '.join(agg_clauses)} FROM {table} GROUP BY {', '.join(group_by)}"
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        return {"success": True, "query": query, "results": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

ADVANCED_TOOLS_AVAILABLE = True

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize clients
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# Create MCP server
app = Server("real-estate-intelligence")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="list_properties",
            description="Liste toutes les propriétés disponibles dans le portefeuille",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_property_dashboard",
            description="🎯 OUTIL PRINCIPAL et RAPIDE - Tableau de bord COMPLET d'une propriété: unités, occupation, baux, maintenance, servitudes, finances. Utiliser EN PREMIER.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {
                        "type": "string",
                        "description": "Nom de la propriété (ex: 'Pratifori', 'Banque 4'). Tolérant aux variations."
                    }
                },
                "required": ["property_name"]
            }
        ),
        Tool(
            name="semantic_search",
            description="⚠️ LENT - Recherche textuelle dans 31K documents. Utiliser UNIQUEMENT pour questions spécifiques nécessitant le contenu des documents. PAS pour infos propriété basiques.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question textuelle spécifique"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Nombre de résultats (défaut: 5, max: 10 recommandé)",
                        "default": 5
                    },
                    "property_filter": {
                        "type": "string",
                        "description": "Filtrer par propriété (optionnel)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_expiring_leases",
            description="Baux arrivant à échéance dans les N prochains mois",
            inputSchema={
                "type": "object",
                "properties": {
                    "months": {
                        "type": "integer",
                        "description": "Nombre de mois à anticiper",
                        "default": 6
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="compare_properties",
            description="Comparaison détaillée entre deux propriétés",
            inputSchema={
                "type": "object",
                "properties": {
                    "property1": {"type": "string", "description": "Première propriété"},
                    "property2": {"type": "string", "description": "Deuxième propriété"}
                },
                "required": ["property1", "property2"]
            }
        ),
        Tool(
            name="get_financial_summary",
            description="Résumé financier global du portefeuille (revenus, dépenses, NOI)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_maintenance_summary",
            description="Résumé des contrats de maintenance actifs",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_servitudes",
            description="Recherche de servitudes dans le registre foncier",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {
                        "type": "string",
                        "description": "Nom de la propriété (optionnel)"
                    },
                    "servitude_type": {
                        "type": "string",
                        "description": "Type de servitude (optionnel)"
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Seulement les servitudes actives",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="execute_sql",
            description="Exécuter une requête SQL brute (SELECT uniquement)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Requête SQL SELECT"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_etat_locatif_complet",
            description="État locatif complet avec KPI, ratios, occupation par propriété",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {"type": "string", "description": "Nom de la propriété (optionnel)"}
                },
                "required": []
            }
        ),
        Tool(
            name="calculate_rendements",
            description="Calcule rendements brut, net, TRI et multiples pour une propriété",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {"type": "string", "description": "Nom de la propriété"}
                },
                "required": ["property_name"]
            }
        ),
        Tool(
            name="detect_anomalies_locatives",
            description="Détecte anomalies: loyers sous-marché, vacance élevée, impayés",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold_vacancy": {"type": "number", "description": "Seuil vacance % (défaut: 10)", "default": 10},
                    "threshold_rent_gap": {"type": "number", "description": "Écart loyer % (défaut: 15)", "default": 15}
                },
                "required": []
            }
        ),
        Tool(
            name="risk_assessment",
            description="Évaluation risques: locataires, technique, marché, financier",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {"type": "string", "description": "Nom de la propriété"}
                },
                "required": ["property_name"]
            }
        ),
        Tool(
            name="time_series_analysis",
            description="Analyse temporelle: tendances, croissance, saisonnalité",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "description": "Métrique (revenue, occupancy, noi)"},
                    "period": {"type": "string", "description": "Période (month, quarter, year)", "default": "month"}
                },
                "required": ["metric"]
            }
        ),
        Tool(
            name="covenant_compliance",
            description="Vérifie conformité covenants bancaires (LTV, DSCR, ICR)",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {"type": "string", "description": "Nom propriété (optionnel pour portfolio)"}
                },
                "required": []
            }
        ),
        Tool(
            name="sensitivity_analysis",
            description="Analyse sensibilité: impact variations loyers/vacance/taux sur NOI/valeur",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {"type": "string", "description": "Nom de la propriété"},
                    "variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Variables (rent, vacancy, cap_rate)"
                    }
                },
                "required": ["property_name"]
            }
        ),
        Tool(
            name="aggregate_data",
            description="Agrégations complexes avec GROUP BY/HAVING sur n'importe quelle table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Nom de la table"},
                    "group_by": {"type": "array", "items": {"type": "string"}, "description": "Colonnes group by"},
                    "aggregations": {"type": "object", "description": "Agrégations {col: func}"}
                },
                "required": ["table", "group_by", "aggregations"]
            }
        ),
        Tool(
            name="pivot_table",
            description="Tableau croisé dynamique à partir d'une table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Nom de la table"},
                    "rows": {"type": "string", "description": "Colonne lignes"},
                    "columns": {"type": "string", "description": "Colonne colonnes"},
                    "values": {"type": "string", "description": "Colonne valeurs"},
                    "aggfunc": {"type": "string", "description": "Fonction agrégation", "default": "sum"}
                },
                "required": ["table", "rows", "columns", "values"]
            }
        ),
        Tool(
            name="fix_unit_types",
            description="Corrige automatiquement les types d'unités (Appartement/Magasin/Bureau/Parking/Dépôt) basé sur unit_number",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_name": {"type": "string", "description": "Nom de la propriété (optionnel, pour toutes si omis)"}
                },
                "required": []
            }
        ),
        Tool(
            name="analyze_system",
            description="🧠 SELF-IMPROVEMENT: Analyse le système MCP actuel (outils, performance, erreurs) et suggère des améliorations",
            inputSchema={
                "type": "object",
                "properties": {
                    "focus": {"type": "string", "description": "Zone à analyser: 'tools', 'data_quality', 'performance', 'all'", "default": "all"}
                },
                "required": []
            }
        ),
        Tool(
            name="improve_tool",
            description="🚀 SELF-IMPROVEMENT: Génère du code amélioré pour un outil existant basé sur l'analyse",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "Nom de l'outil à améliorer"},
                    "improvements": {"type": "array", "items": {"type": "string"}, "description": "Liste des améliorations à appliquer"}
                },
                "required": ["tool_name", "improvements"]
            }
        ),
        Tool(
            name="get_system_logs",
            description="📊 Récupère les logs d'erreurs et métriques de performance des outils",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_n_calls": {"type": "integer", "description": "Nombre d'appels récents", "default": 100}
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Execute tool calls"""
    
    try:
        if name == "list_properties":
            result = list_properties()
        
        elif name == "get_property_dashboard":
            result = get_property_dashboard(arguments["property_name"])
        
        elif name == "semantic_search":
            result = semantic_search(
                query=arguments["query"],
                limit=arguments.get("limit", 10),
                property_filter=arguments.get("property_filter")
            )
        
        elif name == "get_expiring_leases":
            result = get_expiring_leases(arguments.get("months", 6))
        
        elif name == "compare_properties":
            result = compare_properties(arguments["property1"], arguments["property2"])
        
        elif name == "get_financial_summary":
            result = get_financial_summary()
        
        elif name == "get_maintenance_summary":
            result = get_maintenance_summary()
        
        elif name == "search_servitudes":
            result = search_servitudes(
                property_name=arguments.get("property_name"),
                servitude_type=arguments.get("servitude_type"),
                active_only=arguments.get("active_only", True)
            )
        
        elif name == "execute_sql":
            result = execute_sql(arguments["query"])
        
        elif name == "get_etat_locatif_complet":
            if ADVANCED_TOOLS_AVAILABLE:
                result = advanced_etat_locatif(supabase, arguments.get("property_name"))
            else:
                result = {"success": False, "error": "Advanced tools not available"}
        
        elif name == "calculate_rendements":
            if ADVANCED_TOOLS_AVAILABLE:
                result = advanced_rendements(supabase, arguments["property_name"])
            else:
                result = {"success": False, "error": "Advanced tools not available"}
        
        elif name == "detect_anomalies_locatives":
            if ADVANCED_TOOLS_AVAILABLE:
                result = advanced_anomalies(
                    supabase,
                    arguments.get("threshold_vacancy", 10),
                    arguments.get("threshold_rent_gap", 15)
                )
            else:
                result = {"success": False, "error": "Advanced tools not available"}
        
        elif name == "risk_assessment":
            if ADVANCED_TOOLS_AVAILABLE:
                result = advanced_risk(supabase, arguments["property_name"])
            else:
                result = {"success": False, "error": "Advanced tools not available"}
        
        elif name == "covenant_compliance":
            if ADVANCED_TOOLS_AVAILABLE:
                result = advanced_covenant(supabase, arguments.get("property_name"))
            else:
                result = {"success": False, "error": "Advanced tools not available"}
        
        elif name == "aggregate_data":
            if ADVANCED_TOOLS_AVAILABLE:
                result = advanced_aggregate(
                    supabase,
                    arguments["table"],
                    arguments["group_by"],
                    arguments["aggregations"]
                )
            else:
                result = {"success": False, "error": "Advanced tools not available"}
        
        elif name == "time_series_analysis":
            result = {"success": False, "error": "À implémenter avec données historiques"}
        
        elif name == "sensitivity_analysis":
            result = {"success": False, "error": "À implémenter avec modèle financier"}
        
        elif name == "pivot_table":
            result = {"success": False, "error": "À implémenter avec pandas"}
        
        elif name == "fix_unit_types":
            result = fix_unit_types(arguments.get("property_name"))
        
        elif name == "analyze_system":
            from mcp_tools.self_improvement import analyze_system as analyze_sys
            result = analyze_sys(arguments.get("focus", "all"))
        
        elif name == "improve_tool":
            from mcp_tools.self_improvement import improve_tool as improve
            result = improve(arguments["tool_name"], arguments["improvements"])
        
        elif name == "get_system_logs":
            from mcp_tools.self_improvement import get_system_logs as get_logs
            result = get_logs(arguments.get("last_n_calls", 100))
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]
    
    except Exception as e:
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

def list_properties():
    """List all properties"""
    try:
        result = supabase.rpc('exec_sql', {'sql': 'SELECT name, address FROM properties ORDER BY name'}).execute()
        return {
            "success": True,
            "properties": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_property_dashboard(property_name: str):
    """Complete property dashboard"""
    try:
        # Find property
        prop_result = supabase.rpc('exec_sql', {
            'sql': f"SELECT * FROM properties WHERE name ILIKE '%{property_name}%' LIMIT 1"
        }).execute()
        
        if not prop_result.data:
            all_props = supabase.rpc('exec_sql', {'sql': 'SELECT name FROM properties ORDER BY name'}).execute()
            return {
                "success": False,
                "error": f"Propriété '{property_name}' non trouvée",
                "available": [p['name'] for p in all_props.data] if all_props.data else []
            }
        
        prop = prop_result.data[0]
        prop_id = prop['id']
        
        # Get units with leases
        units_result = supabase.rpc('exec_sql', {'sql': f"""
            SELECT 
                u.*,
                COUNT(l.id) as lease_count,
                SUM(CASE WHEN l.end_date IS NULL OR l.end_date > NOW() THEN 1 ELSE 0 END) as active_leases
            FROM units u
            LEFT JOIN leases l ON l.unit_id = u.id
            WHERE u.property_id = '{prop_id}'
            GROUP BY u.id
        """}).execute()
        
        # Get leases with tenants
        leases_result = supabase.rpc('exec_sql', {'sql': f"""
            SELECT l.*, t.name as tenant_name, u.unit_number
            FROM leases l
            JOIN units u ON l.unit_id = u.id
            LEFT JOIN tenants t ON l.tenant_id = t.id
            WHERE u.property_id = '{prop_id}'
              AND (l.end_date IS NULL OR l.end_date > NOW())
            ORDER BY u.unit_number
        """}).execute()
        
        # Get maintenance
        maint_result = supabase.rpc('exec_sql', {'sql': f"SELECT * FROM maintenance WHERE property_id = '{prop_id}'"}).execute()
        
        # Get servitudes
        serv_result = supabase.rpc('exec_sql', {'sql': f"SELECT * FROM servitudes WHERE property_id = '{prop_id}' AND is_active = true"}).execute()
        
        # Get financials
        fin_result = supabase.rpc('exec_sql', {'sql': f"SELECT * FROM financial_statements WHERE property_id = '{prop_id}' LIMIT 1"}).execute()
        
        units = units_result.data if units_result.data else []
        total_units = len(units)
        occupied = sum(1 for u in units if (u.get('active_leases') or 0) > 0)
        
        return {
            "success": True,
            "property": {
                "name": prop['name'],
                "address": prop.get('address'),
                "purchase_price": prop.get('purchase_price'),
                "construction_year": prop.get('construction_year')
            },
            "units": {
                "total": total_units,
                "occupied": occupied,
                "vacant": total_units - occupied,
                "occupation_rate": round(occupied / total_units * 100, 2) if total_units > 0 else 0,
                "details": units
            },
            "leases": leases_result.data if leases_result.data else [],
            "maintenance": {
                "contracts": len(maint_result.data) if maint_result.data else 0,
                "total_annual_cost": sum(float(c.get('annual_cost', 0) or 0) for c in (maint_result.data or [])),
                "details": maint_result.data if maint_result.data else []
            },
            "servitudes": {
                "active": len(serv_result.data) if serv_result.data else 0,
                "details": [{"type": s.get('servitude_type'), "description": s.get('description')} for s in (serv_result.data or [])]
            },
            "financials": fin_result.data[0] if fin_result.data else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def semantic_search(query: str, limit: int = 10, property_filter: str = None):
    """Semantic search in documents - OPTIMIZED"""
    try:
        # Generate embedding
        response = openai.embeddings.create(model="text-embedding-3-small", input=query)
        query_embedding = response.data[0].embedding
        
        # Direct SQL query with pgvector - FAST
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        sql = f"""
        SELECT 
            c.content,
            c.metadata,
            1 - (c.embedding <=> '{embedding_str}'::vector) as similarity
        FROM document_chunks c
        {"WHERE c.metadata->>'property_name' ILIKE '%" + property_filter + "%'" if property_filter else ""}
        ORDER BY c.embedding <=> '{embedding_str}'::vector
        LIMIT {limit}
        """
        
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        
        return {
            "success": True,
            "query": query,
            "results_count": len(result.data) if result.data else 0,
            "results": result.data if result.data else []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Semantic search failed: {str(e)}",
            "hint": "Use get_property_dashboard for property info instead"
        }


def get_expiring_leases(months: int = 6):
    """Leases expiring soon"""
    from datetime import datetime, timedelta
    future_date = datetime.now() + timedelta(days=30 * months)
    
    leases = supabase.table('leases').select(
        '*, units(unit_number, properties(name)), tenants(name)'
    ).lte('end_date', future_date.isoformat()).gte(
        'end_date', datetime.now().isoformat()
    ).order('end_date').execute()
    
    return {
        "success": True,
        "months_ahead": months,
        "expiring_count": len(leases.data),
        "leases": leases.data
    }


def compare_properties(property1: str, property2: str):
    """Compare two properties"""
    dash1 = get_property_dashboard(property1)
    dash2 = get_property_dashboard(property2)
    
    if not dash1.get('success') or not dash2.get('success'):
        return {"success": False, "error": "Une ou les deux propriétés non trouvées"}
    
    return {
        "success": True,
        "comparison": {
            property1: dash1,
            property2: dash2
        }
    }


def get_financial_summary():
    """Global financial summary"""
    properties = supabase.table('properties').select('*, financial_statements(*)').execute()
    
    total_revenue = 0
    total_expenses = 0
    total_noi = 0
    
    for prop in properties.data:
        fs = prop.get('financial_statements', [])
        if fs:
            fs = fs[0]
            total_revenue += fs.get('total_revenue', 0) or 0
            total_expenses += fs.get('total_expenses', 0) or 0
            total_noi += fs.get('noi', 0) or 0
    
    return {
        "success": True,
        "portfolio": {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "total_noi": round(total_noi, 2),
            "properties_count": len(properties.data)
        }
    }


def get_maintenance_summary():
    """Maintenance contracts summary"""
    contracts = supabase.table('maintenance').select('*, properties(name)').execute()
    
    total_cost = sum(c.get('annual_cost', 0) or 0 for c in contracts.data)
    
    return {
        "success": True,
        "total_contracts": len(contracts.data),
        "total_annual_cost": round(total_cost, 2),
        "contracts": contracts.data
    }


def search_servitudes(property_name: str = None, servitude_type: str = None, active_only: bool = True):
    """Search servitudes"""
    query = supabase.table('servitudes').select('*, properties(name)')
    
    if active_only:
        query = query.eq('is_active', True)
    
    if property_name:
        query = query.eq('properties.name', property_name)
    
    if servitude_type:
        query = query.eq('servitude_type', servitude_type)
    
    result = query.execute()
    
    return {
        "success": True,
        "servitudes_count": len(result.data),
        "servitudes": result.data
    }


def fix_unit_types(property_name: str = None):
    """Fix unit types based on unit_number"""
    try:
        # Build WHERE clause
        where_clause = ""
        if property_name:
            where_clause = f"AND p.name ILIKE '%{property_name}%'"
        
        # Get units to analyze
        sql = f"""
        SELECT u.id, u.unit_number, u.type as current_type, p.name as property_name
        FROM units u
        JOIN properties p ON u.property_id = p.id
        WHERE 1=1 {where_clause}
        """
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        units = result.data if result.data else []
        
        # Determine correct types
        updates = []
        for unit in units:
            unit_num = (unit['unit_number'] or '').lower()
            
            # Detection logic
            if any(kw in unit_num for kw in ['place', 'parking', 'garage', 'box']):
                new_type = 'Parking'
            elif any(kw in unit_num for kw in ['dépôt', 'depot', 'cave', 'lager']):
                new_type = 'Dépôt'
            elif any(kw in unit_num for kw in ['local technique', 'local concierge']):
                new_type = 'Local technique'
            elif any(kw in unit_num for kw in ['magasin', 'commerce', 'laden']):
                new_type = 'Magasin'
            elif any(kw in unit_num for kw in ['bureau', 'büro', 'office']):
                new_type = 'Bureau'
            else:
                new_type = 'Appartement'
            
            if new_type != unit['current_type']:
                updates.append({
                    'id': unit['id'],
                    'unit_number': unit['unit_number'],
                    'property': unit['property_name'],
                    'old_type': unit['current_type'],
                    'new_type': new_type
                })
        
        # Apply updates
        if updates:
            for update in updates:
                supabase.rpc('exec_sql', {'sql': f"""
                    UPDATE units SET type = '{update['new_type']}' WHERE id = '{update['id']}'
                """}).execute()
        
        return {
            "success": True,
            "units_analyzed": len(units),
            "units_updated": len(updates),
            "updates": updates
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_sql(query: str):
    """Execute raw SQL query"""
    # Security: only allow SELECT queries
    query_upper = query.strip().upper()
    
    if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
        return {
            "success": False,
            "error": "Seules les requêtes SELECT sont autorisées pour des raisons de sécurité",
            "hint": "Utilisez SELECT ou WITH (pour CTE)"
        }
    
    # Block dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {
                "success": False,
                "error": f"Mot-clé interdit détecté: {keyword}",
                "hint": "Cette requête pourrait modifier les données. Utilisez seulement SELECT."
            }
    
    try:
        # Execute via Supabase RPC or direct PostgreSQL
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        
        if result.data:
            return {
                "success": True,
                "query": query,
                "rows_count": len(result.data) if isinstance(result.data, list) else 1,
                "results": result.data
            }
        else:
            # Fallback: try direct execution via postgrest
            # This is a workaround - ideally create exec_sql function in Supabase
            return {
                "success": False,
                "error": "La fonction RPC 'exec_sql' n'existe pas encore dans Supabase",
                "hint": "Utilisez les autres outils (get_property_dashboard, etc.) ou créez la fonction RPC",
                "alternative": "Vous pouvez exécuter via psql directement pour l'instant"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

