from supabase import create_client, Client
import json
from datetime import datetime
from collections import defaultdict

# Configuration
SUPABASE_URL = "https://reqkkltmtaflbkchsmzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_dashboard():
    # Fetch data
    properties = supabase.table("properties").select("*").execute().data
    units = supabase.table("units").select("*").execute().data
    leases = supabase.table("leases").select("*").execute().data
    
    # Calculate metrics
    total_properties = len(properties)
    total_units = len(units)
    total_leases = len(leases)
    occupancy_rate = (total_leases / total_units * 100) if total_units > 0 else 0
    
    total_revenue = sum(l.get('rent_net', 0) + l.get('charges', 0) for l in leases if l.get('rent_net'))
    annualized_revenue = total_revenue * 12
    
    # Property revenue breakdown
    property_data = []
    for prop in properties:
        prop_units = [u for u in units if u.get('property_id') == prop['id']]
        prop_leases = [l for l in leases if any(u['id'] == l.get('unit_id') for u in prop_units)]
        prop_revenue = sum(l.get('rent_net', 0) + l.get('charges', 0) for l in prop_leases if l.get('rent_net'))
        prop_occupancy = (len(prop_leases) / len(prop_units) * 100) if prop_units else 0
        
        property_data.append({
            'name': prop['name'],
            'city': prop.get('city', 'N/A'),
            'revenue': prop_revenue,
            'occupancy': prop_occupancy
        })
    
    property_data.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Generate HTML with Chart.js
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Portfolio Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            color: #667eea;
            font-size: 2.5rem;
            font-weight: bold;
            margin-top: 10px;
        }}
        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}
        .chart-title {{
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }}
        canvas {{
            max-height: 400px;
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 Real Estate Portfolio Dashboard</h1>
        
        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Properties</div>
                <div class="metric-value">{total_properties}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Units</div>
                <div class="metric-value">{total_units}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Occupancy Rate</div>
                <div class="metric-value">{occupancy_rate:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Monthly Revenue</div>
                <div class="metric-value">CHF {total_revenue:,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Annual Revenue</div>
                <div class="metric-value">CHF {annualized_revenue:,.0f}</div>
            </div>
        </div>
        
        <!-- Revenue by Property Chart -->
        <div class="chart-container">
            <div class="chart-title">Revenue by Property</div>
            <canvas id="revenueChart"></canvas>
        </div>
        
        <!-- Occupancy Rate Chart -->
        <div class="chart-container">
            <div class="chart-title">Occupancy Rates</div>
            <canvas id="occupancyChart"></canvas>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        // Revenue by Property
        const revenueCtx = document.getElementById('revenueChart').getContext('2d');
        new Chart(revenueCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([p['name'] for p in property_data])},
                datasets: [{{
                    label: 'Monthly Revenue (CHF)',
                    data: {json.dumps([p['revenue'] for p in property_data])},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return 'CHF ' + value.toLocaleString();
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Occupancy Rates
        const occupancyCtx = document.getElementById('occupancyChart').getContext('2d');
        new Chart(occupancyCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps([p['name'] for p in property_data])},
                datasets: [{{
                    label: 'Occupancy (%)',
                    data: {json.dumps([p['occupancy'] for p in property_data])},
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(199, 199, 199, 0.8)',
                        'rgba(83, 102, 255, 0.8)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'right'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """
    
    # Save dashboard
    with open("portfolio_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ Dashboard generated: portfolio_dashboard.html")
    print(f"📊 Key Metrics:")
    print(f"   - Properties: {total_properties}")
    print(f"   - Units: {total_units}")
    print(f"   - Occupancy: {occupancy_rate:.1f}%")
    print(f"   - Annual Revenue: CHF {annualized_revenue:,.0f}")

if __name__ == "__main__":
    generate_dashboard()
