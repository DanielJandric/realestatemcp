"""
MCP Tool: Property Analytics & Reporting
Sophisticated analytics for MCP with direct database access
"""
import os
from supabase import create_client
from typing import Dict, List, Optional
from datetime import datetime, timedelta

DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase = create_client(DATABASE_URL, SUPABASE_KEY)


def get_property_dashboard(property_name: str) -> Dict:
    """
    Complete dashboard for a property
    
    Returns:
        Comprehensive property data including financials, units, servitudes
    
    Example:
        dashboard = get_property_dashboard("Pratifori 5-7")
    """
    
    # Get property
    prop = supabase.table('properties').select('*').eq('name', property_name).single().execute()
    if not prop.data:
        return {'error': 'Property not found'}
    
    prop_id = prop.data['id']
    
    # Get units
    units = supabase.table('units').select('*').eq('property_id', prop_id).execute()
    
    # Get active leases
    leases = supabase.table('leases')\
        .select('*, units(*), tenants(*)')\
        .eq('property_id', prop_id)\
        .eq('status', 'active')\
        .execute()
    
    # Get servitudes
    servitudes = supabase.table('servitudes')\
        .select('*')\
        .eq('property_id', prop_id)\
        .eq('statut', 'active')\
        .execute()
    
    # Get maintenance
    maintenance = supabase.table('maintenance')\
        .select('*')\
        .eq('property_id', prop_id)\
        .execute()
    
    # Calculate metrics
    total_units = len(units.data)
    occupied_units = len(leases.data)
    occupation_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    monthly_revenue = sum(l.get('rent_net', 0) for l in leases.data)
    annual_revenue = monthly_revenue * 12
    
    maintenance_costs = sum(m.get('annual_cost', 0) for m in maintenance.data)
    net_revenue = annual_revenue - maintenance_costs
    
    critical_servitudes = len([s for s in servitudes.data if s.get('importance_niveau') == 'critique'])
    
    return {
        'property': {
            'name': prop.data['name'],
            'address': prop.data.get('address'),
            'purchase_price': prop.data.get('purchase_price'),
            'year_built': prop.data.get('year_built')
        },
        'metrics': {
            'total_units': total_units,
            'occupied_units': occupied_units,
            'occupation_rate': round(occupation_rate, 1),
            'monthly_revenue': round(monthly_revenue, 2),
            'annual_revenue': round(annual_revenue, 2),
            'maintenance_costs': round(maintenance_costs, 2),
            'net_revenue': round(net_revenue, 2),
            'roi_percent': round((net_revenue / prop.data.get('purchase_price', 1)) * 100, 2) if prop.data.get('purchase_price') else None
        },
        'units_by_type': self._count_by_field(units.data, 'type'),
        'servitudes': {
            'total': len(servitudes.data),
            'critical': critical_servitudes,
            'by_type': self._count_by_field(servitudes.data, 'type_servitude')
        },
        'maintenance_contracts': len(maintenance.data)
    }

def _count_by_field(data: List[Dict], field: str) -> Dict:
    """Helper to count occurrences"""
    counts = {}
    for item in data:
        value = item.get(field, 'Unknown')
        counts[value] = counts.get(value, 0) + 1
    return counts


def compare_properties() -> List[Dict]:
    """
    Compare all properties side-by-side
    
    Returns:
        List of properties with key metrics
    """
    
    properties = supabase.table('properties').select('*').execute()
    
    results = []
    for prop in properties.data:
        prop_id = prop['id']
        
        # Get counts
        units_count = supabase.table('units').select('id', count='exact').eq('property_id', prop_id).execute().count
        
        leases_count = supabase.table('leases').select('id', count='exact')\
            .eq('property_id', prop_id)\
            .eq('status', 'active')\
            .execute().count
        
        servitudes_count = supabase.table('servitudes').select('id', count='exact')\
            .eq('property_id', prop_id)\
            .eq('statut', 'active')\
            .execute().count
        
        occupation_rate = (leases_count / units_count * 100) if units_count > 0 else 0
        
        results.append({
            'name': prop['name'],
            'units': units_count,
            'occupied': leases_count,
            'occupation_rate': round(occupation_rate, 1),
            'annual_rent': prop.get('total_annual_rent', 0),
            'servitudes': servitudes_count,
            'purchase_price': prop.get('purchase_price')
        })
    
    # Sort by annual rent
    results.sort(key=lambda x: x['annual_rent'] or 0, reverse=True)
    
    return results


def get_expiring_leases(months: int = 6) -> List[Dict]:
    """
    Get leases expiring within specified months
    
    Args:
        months: Number of months to look ahead (default 6)
    
    Returns:
        List of expiring leases with details
    """
    
    from datetime import datetime, timedelta
    
    end_date = datetime.now() + timedelta(days=30 * months)
    
    leases = supabase.table('leases')\
        .select('*, units(number, type), properties(name), tenants(name)')\
        .eq('status', 'active')\
        .lte('end_date', end_date.isoformat())\
        .gte('end_date', datetime.now().isoformat())\
        .execute()
    
    results = []
    for lease in leases.data:
        end_date_obj = datetime.fromisoformat(lease['end_date'].replace('Z', '+00:00'))
        days_remaining = (end_date_obj - datetime.now()).days
        
        results.append({
            'property': lease.get('properties', {}).get('name'),
            'unit': lease.get('units', {}).get('number'),
            'tenant': lease.get('tenants', {}).get('name'),
            'end_date': lease['end_date'],
            'days_remaining': days_remaining,
            'rent_net': lease.get('rent_net')
        })
    
    # Sort by days remaining
    results.sort(key=lambda x: x['days_remaining'])
    
    return results


def get_servitudes_by_importance() -> Dict:
    """
    Group servitudes by importance level across all properties
    
    Returns:
        Servitudes organized by importance with property details
    """
    
    servitudes = supabase.table('servitudes')\
        .select('*, properties(name)')\
        .eq('statut', 'active')\
        .execute()
    
    by_importance = {
        'critique': [],
        'importante': [],
        'normale': [],
        'mineure': []
    }
    
    for serv in servitudes.data:
        level = serv.get('importance_niveau', 'normale')
        
        by_importance[level].append({
            'property': serv.get('properties', {}).get('name'),
            'type': serv.get('type_servitude'),
            'description': serv.get('description', '')[:150],
            'impact_construction': serv.get('impact_constructibilite'),
            'impact_usage': serv.get('impact_usage'),
            'date_inscription': str(serv.get('date_inscription'))
        })
    
    # Add counts
    summary = {
        level: {
            'count': len(items),
            'servitudes': items
        }
        for level, items in by_importance.items()
    }
    
    return summary


def get_maintenance_summary() -> Dict:
    """
    Summary of all maintenance contracts
    
    Returns:
        Maintenance contracts organized by property with costs
    """
    
    maintenance = supabase.table('maintenance')\
        .select('*, properties(name)')\
        .execute()
    
    by_property = {}
    total_annual_cost = 0
    
    for contract in maintenance.data:
        prop_name = contract.get('properties', {}).get('name', 'Unknown')
        
        if prop_name not in by_property:
            by_property[prop_name] = {
                'contracts': [],
                'total_cost': 0
            }
        
        annual_cost = contract.get('annual_cost', 0) or 0
        
        by_property[prop_name]['contracts'].append({
            'vendor': contract.get('vendor_name'),
            'type': contract.get('contract_type'),
            'annual_cost': annual_cost,
            'start_date': str(contract.get('start_date')),
            'end_date': str(contract.get('end_date'))
        })
        
        by_property[prop_name]['total_cost'] += annual_cost
        total_annual_cost += annual_cost
    
    return {
        'total_annual_cost': round(total_annual_cost, 2),
        'by_property': by_property,
        'total_contracts': len(maintenance.data)
    }


def get_financial_summary() -> Dict:
    """
    Complete financial overview across all properties
    
    Returns:
        Aggregated financial data
    """
    
    # Get all properties
    properties = supabase.table('properties').select('*').execute()
    
    # Get all active leases
    leases = supabase.table('leases')\
        .select('rent_net, rent_charges')\
        .eq('status', 'active')\
        .execute()
    
    # Get all maintenance
    maintenance = supabase.table('maintenance')\
        .select('annual_cost')\
        .execute()
    
    # Get all insurance
    insurance = supabase.table('insurance_policies')\
        .select('annual_premium')\
        .eq('status', 'active')\
        .execute()
    
    # Calculate
    total_monthly_rent = sum(l.get('rent_net', 0) for l in leases.data)
    total_monthly_charges = sum(l.get('rent_charges', 0) or 0 for l in leases.data)
    total_annual_revenue = (total_monthly_rent + total_monthly_charges) * 12
    
    total_maintenance = sum(m.get('annual_cost', 0) or 0 for m in maintenance.data)
    total_insurance = sum(i.get('annual_premium', 0) or 0 for i in insurance.data)
    
    total_costs = total_maintenance + total_insurance
    net_income = total_annual_revenue - total_costs
    
    total_purchase_price = sum(p.get('purchase_price', 0) or 0 for p in properties.data)
    roi = (net_income / total_purchase_price * 100) if total_purchase_price > 0 else 0
    
    return {
        'revenue': {
            'monthly_rent': round(total_monthly_rent, 2),
            'monthly_charges': round(total_monthly_charges, 2),
            'annual_total': round(total_annual_revenue, 2)
        },
        'costs': {
            'maintenance': round(total_maintenance, 2),
            'insurance': round(total_insurance, 2),
            'total': round(total_costs, 2)
        },
        'net': {
            'annual_income': round(net_income, 2),
            'monthly_income': round(net_income / 12, 2)
        },
        'portfolio': {
            'total_value': round(total_purchase_price, 2),
            'roi_percent': round(roi, 2),
            'properties_count': len(properties.data),
            'active_leases': len(leases.data)
        }
    }


# Example usage
if __name__ == "__main__":
    print("=== Property Dashboard ===")
    dashboard = get_property_dashboard("Pratifori 5-7")
    print(f"Occupation: {dashboard['metrics']['occupation_rate']}%")
    print(f"Annual revenue: CHF {dashboard['metrics']['annual_revenue']}")
    
    print("\n=== Comparison ===")
    comparison = compare_properties()
    for prop in comparison[:3]:
        print(f"{prop['name']}: {prop['occupation_rate']}% occupied")
    
    print("\n=== Financial Summary ===")
    financial = get_financial_summary()
    print(f"Total annual revenue: CHF {financial['revenue']['annual_total']}")
    print(f"Total costs: CHF {financial['costs']['total']}")
    print(f"Net income: CHF {financial['net']['annual_income']}")
    print(f"Portfolio ROI: {financial['portfolio']['roi_percent']}%")

