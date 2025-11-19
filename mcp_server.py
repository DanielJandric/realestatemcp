"""
Enhanced Real Estate MCP Server with Advanced Analytics
Includes all original tools plus new dispute, incident, prediction, and fraud detection tools
"""

from mcp.server.fastmcp import FastMCP
from supabase import create_client, Client
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from typing import List, Dict, Any, Optional

# Import cache and validator
from mcp_cache import cached, invalidate_cache, get_cache_stats
from data_validator import DataValidator, generate_data_quality_report

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize MCP Server
mcp = FastMCP("RealEstateAgent")

# ==================== ORIGINAL RESOURCES & TOOLS ====================

@mcp.resource("properties://list")
@cached(ttl=300)
def list_properties() -> str:
    """List all properties managed by the agency."""
    response = supabase.table("properties").select("*").execute()
    return json.dumps(response.data, indent=2)

@mcp.tool()
@cached(ttl=300)
def search_tenants(query: str) -> str:
    """Search for tenants by name.
    
    Args:
        query: The name or partial name of the tenant to search for.
    """
    response = supabase.table("tenants").select("*").ilike("name", f"%{query}%").execute()
    return json.dumps(response.data, indent=2)

@mcp.tool()
@cached(ttl=300)
def get_tenant_details(tenant_id: str) -> str:
    """Get full details for a specific tenant, including leases and documents.
    
    Args:
        tenant_id: The UUID of the tenant.
    """
    tenant = supabase.table("tenants").select("*").eq("id", tenant_id).single().execute()
    leases = supabase.table("leases").select("*, units(*)").eq("tenant_id", tenant_id).execute()
    documents = supabase.table("documents").select("*").eq("tenant_id", tenant_id).execute()
    
    result = {
        "tenant": tenant.data,
        "leases": leases.data,
        "documents": documents.data
    }
    return json.dumps(result, indent=2)

@mcp.tool()
def query_database(query: str) -> str:
    """Execute a raw SQL query against the database.
    
    Args:
        query: The SQL query to execute.
    """
    try:
        response = supabase.rpc("exec_sql", {"query": query}).execute()
        return json.dumps(response.data, indent=2)
    except Exception as e:
        return f"Error executing query: {str(e)}"

@mcp.tool()
def get_database_schema() -> str:
    """Get the current database schema (tables and columns)."""
    return """
    Tables:
    - properties (id, name, address, city, zip_code)
    - units (id, property_id, unit_number, floor, type, surface_area, rooms)
    - tenants (id, name, email, phone, external_id)
    - leases (id, unit_id, tenant_id, start_date, end_date, rent_net, charges, status)
    - documents (id, tenant_id, lease_id, property_id, file_path, file_name, type, category)
    - disputes (id, property_id, tenant_id, description, status, amount, date)
    - incidents (id, property_id, tenant_id, description, status, date, insurance_ref)
    - maintenance (id, property_id, provider, description, start_date, end_date, cost)
    
    Materialized Views:
    - mv_portfolio_summary (portfolio-wide metrics)
    - mv_property_metrics (per-property performance)
    - mv_unit_type_analysis (unit type comparisons)
    """

@mcp.tool()
@cached(ttl=300)
def get_property_units(property_id: str) -> str:
    """List all units for a specific property.
    
    Args:
        property_id: The UUID of the property.
    """
    response = supabase.table("units").select("*").eq("property_id", property_id).execute()
    return json.dumps(response.data, indent=2)

@mcp.tool()
@cached(ttl=300)
def search_documents(query: str) -> str:
    """Search for documents by filename.
    
    Args:
        query: The filename or partial filename to search for.
    """
    response = supabase.table("documents").select("*").ilike("file_name", f"%{query}%").execute()
    return json.dumps(response.data, indent=2)

@mcp.tool()
@cached(ttl=300)
def analyze_portfolio_performance() -> str:
    """Analyze overall portfolio performance with key metrics."""
    try:
        properties = supabase.table("properties").select("*").execute().data
        units = supabase.table("units").select("*").execute().data
        leases = supabase.table("leases").select("*").execute().data
        
        total_properties = len(properties)
        total_units = len(units)
        total_leases = len(leases)
        occupancy_rate = (total_leases / total_units * 100) if total_units > 0 else 0
        
        total_revenue = sum(l.get('rent_net', 0) + l.get('charges', 0) for l in leases if l.get('rent_net'))
        
        units_with_area = [u for u in units if u.get('surface_area', 0) > 0]
        rent_per_sqm_values = []
        for lease in leases:
            unit = next((u for u in units if u['id'] == lease.get('unit_id')), None)
            if unit and unit.get('surface_area', 0) > 0 and lease.get('rent_net', 0) > 0:
                rent_per_sqm_values.append(lease['rent_net'] / unit['surface_area'])
        
        avg_rent_per_sqm = statistics.mean(rent_per_sqm_values) if rent_per_sqm_values else 0
        
        property_stats = []
        for prop in properties:
            prop_units = [u for u in units if u.get('property_id') == prop['id']]
            prop_leases = [l for l in leases if any(u['id'] == l.get('unit_id') for u in prop_units)]
            prop_revenue = sum(l.get('rent_net', 0) + l.get('charges', 0) for l in prop_leases if l.get('rent_net'))
            prop_occupancy = (len(prop_leases) / len(prop_units) * 100) if prop_units else 0
            
            property_stats.append({
                "name": prop['name'],
                "city": prop.get('city', 'N/A'),
                "units": len(prop_units),
                "occupancy_rate": round(prop_occupancy, 1),
                "monthly_revenue": round(prop_revenue, 2)
            })
        
        result = {
            "summary": {
                "total_properties": total_properties,
                "total_units": total_units,
                "total_leases": total_leases,
                "occupancy_rate_percent": round(occupancy_rate, 1),
                "total_monthly_revenue_chf": round(total_revenue, 2),
                "avg_rent_per_sqm_chf": round(avg_rent_per_sqm, 2)
            },
            "properties": property_stats
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error analyzing portfolio: {str(e)}"

@mcp.tool()
@cached(ttl=300)
def find_rent_anomalies(threshold_percent: float = 30.0) -> str:
    """Find units with unusually high or low rents compared to similar units.
    
    Args:
        threshold_percent: Percentage deviation to flag as anomaly (default 30%)
    """
    try:
        units = supabase.table("units").select("*, properties(name, city)").execute().data
        leases = supabase.table("leases").select("*").execute().data
        
        type_groups = defaultdict(list)
        for lease in leases:
            unit = next((u for u in units if u['id'] == lease.get('unit_id')), None)
            if unit and lease.get('rent_net', 0) > 0:
                unit_type = unit.get('type', 'Unknown')
                surface = unit.get('surface_area', 0)
                size_bracket = "0-50" if surface < 50 else "50-100" if surface < 100 else "100-150" if surface < 150 else "150+"
                group_key = f"{unit_type}_{size_bracket}"
                type_groups[group_key].append({
                    "rent": lease['rent_net'],
                    "unit": unit,
                    "lease": lease
                })
        
        anomalies = []
        for group_key, items in type_groups.items():
            if len(items) < 2:
                continue
            
            rents = [i['rent'] for i in items]
            avg_rent = statistics.mean(rents)
            
            for item in items:
                deviation = ((item['rent'] - avg_rent) / avg_rent * 100) if avg_rent > 0 else 0
                if abs(deviation) >= threshold_percent:
                    anomalies.append({
                        "property": item['unit']['properties']['name'],
                        "city": item['unit']['properties']['city'],
                        "unit_number": item['unit'].get('unit_number'),
                        "type": item['unit'].get('type'),
                        "surface_area": item['unit'].get('surface_area'),
                        "rent_chf": item['rent'],
                        "avg_for_type_chf": round(avg_rent, 2),
                        "deviation_percent": round(deviation, 1),
                        "status": "HIGH" if deviation > 0 else "LOW"
                    })
        
        anomalies.sort(key=lambda x: abs(x['deviation_percent']), reverse=True)
        
        return json.dumps({
            "found": len(anomalies),
            "threshold_percent": threshold_percent,
            "anomalies": anomalies
        }, indent=2)
    except Exception as e:
        return f"Error finding anomalies: {str(e)}"

@mcp.tool()
@cached(ttl=300)
def analyze_payment_patterns() -> str:
    """Analyze payment and lease patterns to identify risks."""
    try:
        leases = supabase.table("leases").select("*, tenants(name), units(unit_number, properties(name))").execute().data
        
        active_leases = [l for l in leases if l.get('start_date')]
        lease_durations = []
        zero_rent_leases = []
        
        for lease in active_leases:
            if lease.get('rent_net', 0) == 0:
                zero_rent_leases.append({
                    "property": lease['units']['properties']['name'] if lease.get('units') and lease['units'].get('properties') else "Unknown",
                    "unit": lease['units']['unit_number'] if lease.get('units') else "Unknown",
                    "tenant": lease['tenants']['name'] if lease.get('tenants') else "Unknown"
                })
            
            if lease.get('start_date') and lease.get('end_date'):
                try:
                    start = datetime.fromisoformat(lease['start_date'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(lease['end_date'].replace('Z', '+00:00'))
                    duration_days = (end - start).days
                    lease_durations.append(duration_days)
                except:
                    pass
        
        avg_duration_days = statistics.mean(lease_durations) if lease_durations else 0
        
        result = {
            "total_leases": len(leases),
            "leases_with_dates": len(lease_durations),
            "avg_lease_duration_days": round(avg_duration_days, 1),
            "avg_lease_duration_years": round(avg_duration_days / 365, 1),
            "zero_rent_count": len(zero_rent_leases),
            "zero_rent_leases": zero_rent_leases[:10]
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error analyzing payment patterns: {str(e)}"

@mcp.tool()
@cached(ttl=600)
def generate_financial_report() -> str:
    """Generate a comprehensive financial report."""
    try:
        properties = supabase.table("properties").select("*").execute().data
        units = supabase.table("units").select("*").execute().data
        leases = supabase.table("leases").select("*").execute().data
        
        revenue_by_property = []
        for prop in properties:
            prop_units = [u for u in units if u.get('property_id') == prop['id']]
            prop_leases = [l for l in leases if any(u['id'] == l.get('unit_id') for u in prop_units)]
            total_rent = sum(l.get('rent_net', 0) for l in prop_leases if l.get('rent_net'))
            total_charges = sum(l.get('charges', 0) for l in prop_leases if l.get('charges'))
            
            revenue_by_property.append({
                "property": prop['name'],
                "city": prop.get('city', 'N/A'),
                "rent_revenue": round(total_rent, 2),
                "charges_revenue": round(total_charges, 2),
                "total_revenue": round(total_rent + total_charges, 2),
                "unit_count": len(prop_units),
                "lease_count": len(prop_leases)
            })
        
        revenue_by_property.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        type_revenue = defaultdict(lambda: {'count': 0, 'revenue': 0})
        for lease in leases:
            unit = next((u for u in units if u['id'] == lease.get('unit_id')), None)
            if unit:
                unit_type = unit.get('type', 'Unknown')
                type_revenue[unit_type]['count'] += 1
                type_revenue[unit_type]['revenue'] += (lease.get('rent_net', 0) + lease.get('charges', 0))
        
        revenue_by_type = [
            {
                "type": utype,
                "lease_count": data['count'],
                "total_revenue": round(data['revenue'], 2),
                "avg_revenue_per_unit": round(data['revenue'] / data['count'], 2) if data['count'] > 0 else 0
            }
            for utype, data in type_revenue.items()
        ]
        revenue_by_type.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        total_rent_revenue = sum(l.get('rent_net', 0) for l in leases if l.get('rent_net'))
        total_charges_revenue = sum(l.get('charges', 0) for l in leases if l.get('charges'))
        
        result = {
            "report_date": datetime.now().isoformat(),
            "summary": {
                "total_rent_revenue": round(total_rent_revenue, 2),
                "total_charges_revenue": round(total_charges_revenue, 2),
                "total_monthly_revenue": round(total_rent_revenue + total_charges_revenue, 2),
                "annualized_revenue": round((total_rent_revenue + total_charges_revenue) * 12, 2)
            },
            "revenue_by_property": revenue_by_property,
            "revenue_by_type": revenue_by_type
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error generating financial report: {str(e)}"

# ==================== NEW DISPUTE & INCIDENT TOOLS ====================

@mcp.tool()
@cached(ttl=300)
def get_active_disputes() -> str:
    """Get all active disputes with property and tenant details."""
    try:
        disputes = supabase.table("disputes").select(
            "*, properties(name, city), tenants(name, email)"
        ).in_("status", ["open", "in_progress", "pending"]).execute().data
        
        result = {
            "total_active": len(disputes),
            "total_amount": sum(d.get('amount', 0) for d in disputes),
            "disputes": sorted(disputes, key=lambda x: x.get('amount', 0), reverse=True)
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching disputes: {str(e)}"

@mcp.tool()
@cached(ttl=300)
def analyze_incident_trends() -> str:
    """Analyze incidents by property, status, and time trends."""
    try:
        incidents = supabase.table("incidents").select(
            "*, properties(name, city)"
        ).execute().data
        
        # Group by property
        by_property = defaultdict(int)
        by_status = defaultdict(int)
        by_month = defaultdict(int)
        
        for incident in incidents:
            if incident.get('properties'):
                by_property[incident['properties']['name']] += 1
            
            if incident.get('status'):
                by_status[incident['status']] += 1
            
            if incident.get('date'):
                try:
                    date_obj = datetime.fromisoformat(incident['date'].replace('Z', '+00:00'))
                    month_key = date_obj.strftime('%Y-%m')
                    by_month[month_key] += 1
                except:
                    pass
        
        result = {
            "total_incidents": len(incidents),
            "by_property": dict(sorted(by_property.items(), key=lambda x: x[1], reverse=True)),
            "by_status": dict(by_status),
            "monthly_trend": dict(sorted(by_month.items()))
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error analyzing incidents: {str(e)}"

# ==================== PREDICTION & OPTIMIZATION TOOLS ====================

@mcp.tool()
@cached(ttl=600)
def suggest_rent_optimization(unit_id: str) -> str:
    """Suggest optimal rent for a unit based on comparable units.
    
    Args:
        unit_id: UUID of the unit to analyze
    """
    try:
        # Get target unit
        target_unit = supabase.table("units").select(
            "*, properties(name, city)"
        ).eq("id", unit_id).single().execute().data
        
        # Get current lease if any
        current_lease = supabase.table("leases").select("*").eq(
            "unit_id", unit_id
        ).eq("status", "active").execute().data
        
        current_rent = current_lease[0].get('rent_net', 0) if current_lease else 0
        
        # Find comparable units
        comparables = supabase.table("units").select(
            "*, properties(city), leases!inner(rent_net, status)"
        ).eq("type", target_unit.get('type')).eq(
            "leases.status", "active"
        ).execute().data
        
        # Filter by similar size (±20%)
        target_area = target_unit.get('surface_area', 0)
        if target_area > 0:
            comparables = [
                u for u in comparables 
                if u.get('surface_area', 0) > 0 
                and abs(u['surface_area'] - target_area) / target_area <= 0.2
            ]
        
        # Calculate statistics
        comp_rents = [u['leases'][0]['rent_net'] for u in comparables if u.get('leases')]
        
        if comp_rents:
            suggested_rent = statistics.median(comp_rents)
            avg_rent = statistics.mean(comp_rents)
            min_rent = min(comp_rents)
            max_rent = max(comp_rents)
            
            result = {
                "unit": {
                    "property": target_unit['properties']['name'],
                    "city": target_unit['properties']['city'],
                    "type": target_unit.get('type'),
                    "surface_area": target_unit.get('surface_area'),
                    "current_rent": current_rent
                },
                "recommendation": {
                    "suggested_rent": round(suggested_rent, 2),
                    "potential_change": round(suggested_rent - current_rent, 2),
                    "potential_change_percent": round((suggested_rent - current_rent) / current_rent * 100, 1) if current_rent > 0 else 0
                },
                "market_data": {
                    "comparables_count": len(comp_rents),
                    "avg_rent": round(avg_rent, 2),
                    "median_rent": round(suggested_rent, 2),
                    "min_rent": round(min_rent, 2),
                    "max_rent": round(max_rent, 2)
                }
            }
        else:
            result = {
                "unit": target_unit,
                "error": "No comparable units found"
            }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error suggesting rent optimization: {str(e)}"

@mcp.tool()
@cached(ttl=600)
def predict_vacancy_risk() -> str:
    """Predict vacancy risk for units based on lease end dates and patterns."""
    try:
        leases = supabase.table("leases").select(
            "*, units(unit_number, type, properties(name, city))"
        ).eq("status", "active").execute().data
        
        today = datetime.now()
        risk_units = []
        
        for lease in leases:
            if not lease.get('end_date'):
                continue
            
            try:
                end_date = datetime.fromisoformat(lease['end_date'].replace('Z', '+00:00'))
                days_until_end = (end_date - today).days
                
                # Calculate risk score
                risk_score = 0
                risk_factors = []
                
                if days_until_end <= 90:
                    risk_score += 40
                    risk_factors.append(f"Ending in {days_until_end} days")
                elif days_until_end <= 180:
                    risk_score += 20
                    risk_factors.append(f"Ending in {days_until_end} days")
                
                # Check rent vs market
                unit_type = lease['units'].get('type') if lease.get('units') else None
                if unit_type:
                    # Simple heuristic: very low rent might indicate dissatisfaction
                    if lease.get('rent_net', 0) < 800:  # Arbitrary threshold
                        risk_score += 15
                        risk_factors.append("Below market rent")
                
                if risk_score > 0:
                    risk_units.append({
                        "property": lease['units']['properties']['name'] if lease.get('units') and lease['units'].get('properties') else "Unknown",
                        "city": lease['units']['properties']['city'] if lease.get('units') and lease['units'].get('properties') else "Unknown",
                        "unit_number": lease['units']['unit_number'] if lease.get('units') else "Unknown",
                        "end_date": lease['end_date'],
                        "days_until_end": days_until_end,
                        "risk_score": risk_score,
                        "risk_level": "HIGH" if risk_score >= 50 else "MEDIUM" if risk_score >= 30 else "LOW",
                        "risk_factors": risk_factors
                    })
            except:
                pass
        
        risk_units.sort(key=lambda x: x['risk_score'], reverse=True)
        
        result = {
            "total_at_risk": len(risk_units),
            "high_risk": len([u for u in risk_units if u['risk_level'] == 'HIGH']),
            "medium_risk": len([u for u in risk_units if u['risk_level'] == 'MEDIUM']),
            "units": risk_units
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error predicting vacancy risk: {str(e)}"

# ==================== FRAUD DETECTION ====================

@mcp.tool()
@cached(ttl=600)
def detect_fraud_patterns() -> str:
    """Detect potentially fraudulent patterns in leases and payments."""
    try:
        leases = supabase.table("leases").select(
            "*, tenants(name, email, phone), units(unit_number, properties(name))"
        ).execute().data
        
        suspicious = []
        
        # Check for duplicate tenant information
        email_map = defaultdict(list)
        phone_map = defaultdict(list)
        
        for lease in leases:
            if lease.get('tenants'):
                tenant = lease['tenants']
                if tenant.get('email'):
                    email_map[tenant['email']].append(lease)
                if tenant.get('phone'):
                    phone_map[tenant['phone']].append(lease)
        
        # Multiple active leases with same contact info
        for email, lease_list in email_map.items():
            active = [l for l in lease_list if l.get('status') == 'active']
            if len(active) > 1:
                suspicious.append({
                    "type": "DUPLICATE_EMAIL",
                    "email": email,
                    "active_leases": len(active),
                    "severity": "HIGH",
                    "description": f"Same email used for {len(active)} active leases"
                })
        
        # Unusual rent amounts (suspiciously round numbers for large amounts)
        for lease in leases:
            rent = lease.get('rent_net', 0)
            if rent > 0:
                # Check for very round numbers over 2000
                if rent >= 2000 and rent % 100 == 0:
                    suspicious.append({
                        "type": "SUSPICIOUS_RENT",
                        "lease_id": lease['id'],
                        "property": lease['units']['properties']['name'] if lease.get('units') and lease['units'].get('properties') else "Unknown",
                        "rent": rent,
                        "severity": "LOW",
                        "description": f"Unusually round rent amount: {rent}"
                    })
        
        # Zero deposit leases
        zero_deposit = [l for l in leases if l.get('deposit', 0) == 0 and l.get('rent_net', 0) > 1000]
        for lease in zero_deposit[:10]:  # Limit results
            suspicious.append({
                "type": "ZERO_DEPOSIT",
                "lease_id": lease['id'],
                "property": lease['units']['properties']['name'] if lease.get('units') and lease['units'].get('properties') else "Unknown",
                "rent": lease.get('rent_net'),
                "severity": "MEDIUM",
                "description": "High rent with zero deposit"
            })
        
        result = {
            "total_suspicious": len(suspicious),
            "high_severity": len([s for s in suspicious if s['severity'] == 'HIGH']),
            "medium_severity": len([s for s in suspicious if s['severity'] == 'MEDIUM']),
            "patterns": suspicious
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error detecting fraud: {str(e)}"

# ==================== BENCHMARKING & COMPARISON ====================

@mcp.tool()
@cached(ttl=600)
def compare_property_performance(property_ids: str) -> str:
    """Compare performance of multiple properties.
    
    Args:
        property_ids: Comma-separated list of property UUIDs
    """
    try:
        ids = [pid.strip() for pid in property_ids.split(',')]
        
        comparisons = []
        for prop_id in ids:
            # Get property
            prop = supabase.table("properties").select("*").eq("id", prop_id).single().execute().data
            
            # Get units
            units = supabase.table("units").select("*").eq("property_id", prop_id).execute().data
            
            # Get active leases
            unit_ids = [u['id'] for u in units]
            leases = supabase.table("leases").select("*").in_("unit_id", unit_ids).eq("status", "active").execute().data
            
            # Calculate metrics
            total_rent = sum(l.get('rent_net', 0) for l in leases)
            total_charges = sum(l.get('charges', 0) for l in leases)
            occupancy = (len(leases) / len(units) * 100) if units else 0
            
            # Get disputes and incidents
            disputes = supabase.table("disputes").select("*").eq("property_id", prop_id).in_(
                "status", ["open", "in_progress"]
            ).execute().data
            
            incidents = supabase.table("incidents").select("*").eq("property_id", prop_id).execute().data
            
            comparisons.append({
                "property_id": prop_id,
                "name": prop['name'],
                "city": prop.get('city'),
                "metrics": {
                    "total_units": len(units),
                    "occupied_units": len(leases),
                    "occupancy_rate": round(occupancy, 1),
                    "monthly_revenue": round(total_rent + total_charges, 2),
                    "avg_rent_per_unit": round(total_rent / len(leases), 2) if leases else 0,
                    "active_disputes": len(disputes),
                    "total_incidents": len(incidents)
                }
            })
        
        return json.dumps({"properties": comparisons}, indent=2)
    except Exception as e:
        return f"Error comparing properties: {str(e)}"

@mcp.tool()
@cached(ttl=600)
def benchmark_by_city(city: str) -> str:
    """Benchmark properties in a specific city.
    
    Args:
        city: City name to benchmark
    """
    try:
        properties = supabase.table("properties").select("*").ilike("city", f"%{city}%").execute().data
        
        if not properties:
            return json.dumps({"error": f"No properties found in {city}"}, indent=2)
        
        all_metrics = []
        for prop in properties:
            units = supabase.table("units").select("*").eq("property_id", prop['id']).execute().data
            unit_ids = [u['id'] for u in units]
            
            if unit_ids:
                leases = supabase.table("leases").select("*").in_("unit_id", unit_ids).eq("status", "active").execute().data
                
                total_rent = sum(l.get('rent_net', 0) for l in leases)
                occupancy = (len(leases) / len(units) * 100) if units else 0
                
                all_metrics.append({
                    "property": prop['name'],
                    "occupancy": occupancy,
                    "monthly_revenue": total_rent,
                    "unit_count": len(units)
                })
        
        if all_metrics:
            avg_occupancy = statistics.mean([m['occupancy'] for m in all_metrics])
            avg_revenue = statistics.mean([m['monthly_revenue'] for m in all_metrics])
            
            result = {
                "city": city,
                "total_properties": len(properties),
                "benchmarks": {
                    "avg_occupancy_rate": round(avg_occupancy, 1),
                    "avg_monthly_revenue": round(avg_revenue, 2),
                    "total_units": sum(m['unit_count'] for m in all_metrics)
                },
                "properties": all_metrics
            }
        else:
            result = {"error": "No metrics available"}
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error benchmarking: {str(e)}"

# ==================== MAINTENANCE TOOLS ====================

@mcp.tool()
@cached(ttl=300)
def get_upcoming_maintenance() -> str:
    """Get maintenance contracts expiring within 90 days."""
    try:
        today = datetime.now().date()
        future_90 = today + timedelta(days=90)
        
        maintenance = supabase.table("maintenance").select(
            "*, properties(name, city)"
        ).execute().data
        
        upcoming = []
        for maint in maintenance:
            if maint.get('end_date'):
                try:
                    end_date = datetime.fromisoformat(maint['end_date'].replace('Z', '+00:00')).date()
                    if today <= end_date <= future_90:
                        days_until = (end_date - today).days
                        upcoming.append({
                            "property": maint['properties']['name'] if maint.get('properties') else "Unknown",
                            "provider": maint.get('provider'),
                            "description": maint.get('description'),
                            "end_date": maint['end_date'],
                            "days_until_expiry": days_until,
                            "cost": maint.get('cost')
                        })
                except:
                    pass
        
        upcoming.sort(key=lambda x: x['days_until_expiry'])
        
        return json.dumps({
            "total_expiring_soon": len(upcoming),
            "contracts": upcoming
        }, indent=2)
    except Exception as e:
        return f"Error fetching maintenance: {str(e)}"

@mcp.tool()
@cached(ttl=600)
def analyze_maintenance_costs() -> str:
    """Analyze maintenance costs by property."""
    try:
        maintenance = supabase.table("maintenance").select(
            "*, properties(name, city)"
        ).execute().data
        
        by_property = defaultdict(lambda: {'count': 0, 'total_cost': 0, 'contracts': []})
        
        for maint in maintenance:
            if maint.get('properties'):
                prop_name = maint['properties']['name']
                by_property[prop_name]['count'] += 1
                by_property[prop_name]['total_cost'] += maint.get('cost', 0)
                by_property[prop_name]['contracts'].append({
                    "provider": maint.get('provider'),
                    "description": maint.get('description'),
                    "cost": maint.get('cost')
                })
        
        result = {
            "total_contracts": len(maintenance),
            "total_annual_cost": sum(m.get('cost', 0) for m in maintenance),
            "by_property": [
                {
                    "property": prop,
                    "contract_count": data['count'],
                    "total_cost": round(data['total_cost'], 2),
                    "contracts": data['contracts']
                }
                for prop, data in sorted(by_property.items(), key=lambda x: x[1]['total_cost'], reverse=True)
            ]
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error analyzing maintenance costs: {str(e)}"

# ==================== UTILITY TOOLS ====================

@mcp.tool()
def get_data_quality_report() -> str:
    """Generate a comprehensive data quality report."""
    try:
        report = generate_data_quality_report(supabase)
        return json.dumps(report, indent=2)
    except Exception as e:
        return f"Error generating quality report: {str(e)}"

@mcp.tool()
def get_cache_stats() -> str:
    """Get cache performance statistics."""
    stats = get_cache_stats()
    return json.dumps(stats, indent=2)

@mcp.tool()
def clear_cache(pattern: str = None) -> str:
    """Clear cache entries.
    
    Args:
        pattern: Optional pattern to match for selective clearing
    """
    invalidate_cache(pattern)
    return json.dumps({"status": "Cache cleared", "pattern": pattern or "all"}, indent=2)

@mcp.tool()
@cached(ttl=600)
def generate_executive_summary() -> str:
    """Generate an executive summary with all key metrics."""
    try:
        # Portfolio metrics
        portfolio = json.loads(analyze_portfolio_performance())
        
        # Financial report
        financial = json.loads(generate_financial_report())
        
        # Disputes and incidents
        disputes = json.loads(get_active_disputes())
        incidents = json.loads(analyze_incident_trends())
        
        # Vacancy risk
        vacancy = json.loads(predict_vacancy_risk())
        
        # Maintenance
        maint_upcoming = json.loads(get_upcoming_maintenance())
        maint_costs = json.loads(analyze_maintenance_costs())
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "portfolio_overview": portfolio.get('summary'),
            "financial_summary": financial.get('summary'),
            "risk_indicators": {
                "active_disputes": disputes.get('total_active'),
                "total_dispute_amount": disputes.get('total_amount'),
                "total_incidents": incidents.get('total_incidents'),
                "high_vacancy_risk_units": vacancy.get('high_risk'),
                "upcoming_maintenance_expiry": maint_upcoming.get('total_expiring_soon')
            },
            "top_properties_by_revenue": financial.get('revenue_by_property', [])[:5],
            "maintenance_cost_summary": {
                "total_contracts": maint_costs.get('total_contracts'),
                "total_annual_cost": maint_costs.get('total_annual_cost')
            }
        }
        
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error generating executive summary: {str(e)}"

if __name__ == "__main__":
    mcp.run()
