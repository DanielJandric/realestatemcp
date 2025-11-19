from mcp_server import (
    analyze_portfolio_performance,
    find_rent_anomalies,
    analyze_payment_patterns,
    generate_financial_report
)
import json

def test_advanced_analytics():
    print("=== Testing Advanced Analytics Tools ===\n")
    
    # Test 1: Portfolio performance
    print("1. Testing analyze_portfolio_performance()...")
    try:
        result = analyze_portfolio_performance()
        data = json.loads(result)
        print(f"   ✅ Success - Found {data['summary']['total_properties']} properties")
        print(f"   Occupancy: {data['summary']['occupancy_rate_percent']}%")
        print(f"   Monthly Revenue: CHF {data['summary']['total_monthly_revenue_chf']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Rent anomalies
    print("\n2. Testing find_rent_anomalies()...")
    try:
        result = find_rent_anomalies(30.0)
        data = json.loads(result)
        print(f"   ✅ Success - Found {data['found']} anomalies")
        if data['anomalies']:
            print(f"   Top anomaly: {data['anomalies'][0]['property']} - {data['anom alies'][0]['deviation_percent']}%")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Payment patterns
    print("\n3. Testing analyze_payment_patterns()...")
    try:
        result = analyze_payment_patterns()
        data = json.loads(result)
        print(f"   ✅ Success - Average lease duration: {data['avg_lease_duration_years']} years")
        print(f"   Zero-rent leases: {data['zero_rent_count']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Financial report
    print("\n4. Testing generate_financial_report()...")
    try:
        result = generate_financial_report()
        data = json.loads(result)
        print(f"   ✅ Success - Total monthly revenue: CHF {data['summary']['total_monthly_revenue']}")
        print(f"   Annualized: CHF {data['summary']['annualized_revenue']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ All tests complete!")

if __name__ == "__main__":
    test_advanced_analytics()
