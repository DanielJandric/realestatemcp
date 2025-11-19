from mcp_server import list_properties, search_tenants, get_property_units
import json

def test():
    print("Testing list_properties...")
    props = list_properties()
    print(f"Properties found: {len(json.loads(props))}")
    # print(props)

    print("\nTesting search_tenants (query='Grosset')...")
    tenants = search_tenants("Grosset")
    print(f"Tenants found: {len(json.loads(tenants))}")
    print(tenants)

    print("\nTesting get_property_units...")
    # Get first property ID
    props_data = json.loads(props)
    if props_data:
        p_id = props_data[0]['id']
        units = get_property_units(p_id)
        print(f"Units for {props_data[0]['name']}: {len(json.loads(units))}")

if __name__ == "__main__":
    test()
