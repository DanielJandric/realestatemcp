"""
Advanced Real Estate Analysis Tools
Sophisticated analytics for MCP server
"""

from typing import Optional, List, Dict, Any
import json


def get_etat_locatif_complet(supabase, property_name: Optional[str] = None):
    """État locatif complet avec KPI"""
    try:
        if property_name:
            props = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
            if not props.data:
                return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
            property_ids = [p['id'] for p in props.data]
        else:
            props = supabase.table('properties').select('*').execute()
            property_ids = [p['id'] for p in props.data]
        
        results = []
        for prop in props.data:
            prop_id = prop['id']
            
            # Get units and leases
            units = supabase.table('units').select('*, leases(*, tenants(name))').eq('property_id', prop_id).execute()
            
            total_units = len(units.data)
            occupied = sum(1 for u in units.data if u.get('leases'))
            total_surface = sum(u.get('surface_area', 0) or 0 for u in units.data)
            occupied_surface = sum(u.get('surface_area', 0) or 0 for u in units.data if u.get('leases'))
            
            # Calculate rents
            total_rent = 0
            for unit in units.data:
                if unit.get('leases'):
                    for lease in unit['leases']:
                        total_rent += (lease.get('rent_net', 0) or 0) + (lease.get('rent_charges', 0) or 0)
            
            results.append({
                "property": prop['name'],
                "kpi": {
                    "total_units": total_units,
                    "occupied_units": occupied,
                    "vacant_units": total_units - occupied,
                    "occupation_rate": round(occupied / total_units * 100, 2) if total_units > 0 else 0,
                    "total_surface_m2": round(total_surface, 2),
                    "occupied_surface_m2": round(occupied_surface, 2),
                    "surface_occupation_rate": round(occupied_surface / total_surface * 100, 2) if total_surface > 0 else 0,
                    "annual_rent": round(total_rent * 12, 2),
                    "avg_rent_per_m2": round((total_rent * 12) / occupied_surface, 2) if occupied_surface > 0 else 0
                }
            })
        
        return {
            "success": True,
            "properties_count": len(results),
            "etat_locatif": results,
            "portfolio_kpi": {
                "total_units": sum(r['kpi']['total_units'] for r in results),
                "total_occupied": sum(r['kpi']['occupied_units'] for r in results),
                "avg_occupation_rate": round(sum(r['kpi']['occupation_rate'] for r in results) / len(results), 2) if results else 0,
                "total_annual_rent": sum(r['kpi']['annual_rent'] for r in results)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_rendements(supabase, property_name: str):
    """Calcule les rendements"""
    try:
        prop = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
        if not prop.data:
            return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
        
        property_data = prop.data[0]
        prop_id = property_data['id']
        
        # Get financial data
        financials = supabase.table('financial_statements').select('*').eq('property_id', prop_id).execute()
        
        purchase_price = property_data.get('purchase_price', 0) or 0
        
        if financials.data:
            fs = financials.data[0]
            revenue = fs.get('total_revenue', 0) or 0
            expenses = fs.get('total_expenses', 0) or 0
            noi = fs.get('noi', 0) or 0
        else:
            revenue = 0
            expenses = 0
            noi = 0
        
        # Calculate returns
        rendement_brut = (revenue / purchase_price * 100) if purchase_price > 0 else 0
        rendement_net = (noi / purchase_price * 100) if purchase_price > 0 else 0
        
        return {
            "success": True,
            "property": property_data['name'],
            "rendements": {
                "rendement_brut": round(rendement_brut, 2),
                "rendement_net": round(rendement_net, 2),
                "cap_rate": round(rendement_net, 2),
                "revenue_annuel": round(revenue, 2),
                "charges_annuelles": round(expenses, 2),
                "noi": round(noi, 2),
                "valeur_achat": round(purchase_price, 2)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def detect_anomalies_locatives(supabase, threshold_vacancy: float = 10, threshold_rent_gap: float = 15):
    """Détecte les anomalies locatives"""
    try:
        props = supabase.table('properties').select('*').execute()
        anomalies = []
        
        for prop in props.data:
            prop_id = prop['id']
            units = supabase.table('units').select('*, leases(*)').eq('property_id', prop_id).execute()
            
            total = len(units.data)
            occupied = sum(1 for u in units.data if u.get('leases'))
            vacancy_rate = ((total - occupied) / total * 100) if total > 0 else 0
            
            issues = []
            
            if vacancy_rate > threshold_vacancy:
                issues.append(f"Vacance élevée: {round(vacancy_rate, 1)}%")
            
            # Check low rents (simplified - would need market data)
            rents = []
            for unit in units.data:
                if unit.get('leases'):
                    for lease in unit['leases']:
                        rent = lease.get('rent_net', 0) or 0
                        surface = unit.get('surface_area', 0) or 0
                        if surface > 0:
                            rents.append(rent / surface)
            
            if rents:
                avg_rent = sum(rents) / len(rents)
                for i, rent in enumerate(rents):
                    gap = ((avg_rent - rent) / avg_rent * 100) if avg_rent > 0 else 0
                    if gap > threshold_rent_gap:
                        issues.append(f"Loyer {i+1} sous-marché: -{round(gap, 1)}%")
            
            if issues:
                anomalies.append({
                    "property": prop['name'],
                    "vacancy_rate": round(vacancy_rate, 2),
                    "issues": issues
                })
        
        return {
            "success": True,
            "anomalies_found": len(anomalies),
            "anomalies": anomalies
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def risk_assessment(supabase, property_name: str):
    """Évaluation des risques"""
    try:
        prop = supabase.table('properties').select('*').ilike('name', f'%{property_name}%').execute()
        if not prop.data:
            return {"success": False, "error": f"Propriété '{property_name}' non trouvée"}
        
        property_data = prop.data[0]
        prop_id = property_data['id']
        
        # Tenant risk
        units = supabase.table('units').select('*, leases(*, tenants(*))').eq('property_id', prop_id).execute()
        occupied = sum(1 for u in units.data if u.get('leases'))
        vacancy_rate = ((len(units.data) - occupied) / len(units.data) * 100) if units.data else 0
        
        # Technical risk
        construction_year = property_data.get('construction_year')
        age = 2025 - construction_year if construction_year else None
        
        # Financial risk
        financials = supabase.table('financial_statements').select('*').eq('property_id', prop_id).execute()
        noi = financials.data[0].get('noi', 0) if financials.data else 0
        
        risks = {
            "tenant_risk": {
                "level": "HIGH" if vacancy_rate > 15 else "MEDIUM" if vacancy_rate > 5 else "LOW",
                "vacancy_rate": round(vacancy_rate, 2),
                "occupied_units": occupied,
                "total_units": len(units.data)
            },
            "technical_risk": {
                "level": "HIGH" if age and age > 50 else "MEDIUM" if age and age > 30 else "LOW" if age else "UNKNOWN",
                "building_age": age,
                "construction_year": construction_year
            },
            "financial_risk": {
                "level": "HIGH" if noi < 0 else "MEDIUM" if noi < 50000 else "LOW",
                "noi": round(noi, 2)
            }
        }
        
        return {
            "success": True,
            "property": property_data['name'],
            "risks": risks,
            "overall_risk": "HIGH" if any(r['level'] == 'HIGH' for r in risks.values() if isinstance(r, dict)) else "MEDIUM"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def covenant_compliance(supabase, property_name: Optional[str] = None):
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
                fs = financials.data[0]
                noi = fs.get('noi', 0) or 0
                debt = prop.get('mortgage_amount', 0) or 0
                value = prop.get('purchase_price', 0) or 0
                
                ltv = (debt / value * 100) if value > 0 else 0
                dscr = (noi / (debt * 0.05)) if debt > 0 else 0  # Assuming 5% interest
                
                compliant = ltv <= 75 and dscr >= 1.25
                
                results.append({
                    "property": prop['name'],
                    "ltv": round(ltv, 2),
                    "dscr": round(dscr, 2),
                    "compliant": compliant,
                    "warnings": [
                        "LTV > 75%" if ltv > 75 else None,
                        "DSCR < 1.25" if dscr < 1.25 else None
                    ]
                })
        
        return {
            "success": True,
            "properties_checked": len(results),
            "all_compliant": all(r['compliant'] for r in results),
            "compliance": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def aggregate_data(supabase, table: str, group_by: List[str], aggregations: Dict[str, str]):
    """Agrégations complexes"""
    try:
        # Build SQL query
        agg_clauses = []
        for col, func in aggregations.items():
            agg_clauses.append(f"{func}({col}) as {col}_{func}")
        
        group_by_str = ", ".join(group_by)
        agg_str = ", ".join(agg_clauses)
        
        query = f"SELECT {group_by_str}, {agg_str} FROM {table} GROUP BY {group_by_str}"
        
        # Execute via RPC (if available)
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        
        return {
            "success": True,
            "query": query,
            "results": result.data
        }
    except Exception as e:
        return {"success": False, "error": str(e), "hint": "Créer fonction exec_sql dans Supabase"}

