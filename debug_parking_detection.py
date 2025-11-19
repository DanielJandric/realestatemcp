from supabase import create_client
import re

s = create_client('https://reqkkltmtaflbkchsmzb.supabase.co','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWtrbHRtdGFmbGJrY2hzbXpiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ5MTMyNCwiZXhwIjoyMDc5MDY3MzI0fQ._qrlebAY3-Yw6klqZzSot1jZWt9Zm2T8TnXi_AFULhc')

# Get parking docs
docs = s.table('documents').select('*').filter('category','eq','lease').execute().data
parking_docs = [d for d in docs if 'pp' in d['file_name'].lower()]

print(f"Baux PP: {len(parking_docs)}")

# Get units
units = s.table('units').select('unit_number, type').execute().data

# Build lookup
units_by_number = {}
for unit in units:
    unit_num = unit.get('unit_number', '')
    if unit_num:
        units_by_number[unit_num] = unit
        units_by_number[unit_num.replace('.', '')] = unit

print(f"Units indexées: {len(units)}")

# Try to match PP docs
for doc in parking_docs[:3]:
    print(f"\n{'='*60}")
    print(f"Doc: {doc['file_name']}")
    print(f"Path: {doc['file_path']}")
    
    # Extract ref
    ref_match = re.search(r'(\d{5}\.\d{2}\.\d{6})', doc['file_path'])
    if ref_match:
        ref = ref_match.group(1)
        print(f"Ref trouvée: {ref}")
        
        # Check if unit exists
        unit = units_by_number.get(ref)
        if unit:
            print(f"✅ Unit matched: {unit['unit_number']} (type: {unit['type']})")
        else:
            print(f"❌ Unit NOT found for ref: {ref}")
            print(f"   Trying variations...")
            ref_clean = ref.replace('.', '')
            unit2 = units_by_number.get(ref_clean)
            if unit2:
                print(f"   ✅ Found with clean ref: {unit2['unit_number']}")
    else:
        print("❌ No ref found in path")

# Check if these specific units exist
test_refs = ['45638.80.101002', '45638.80.101003']
print(f"\n{'='*60}")
print("Vérification des unités PP spécifiques:")
for ref in test_refs:
    unit = units_by_number.get(ref)
    if unit:
        print(f"✅ {ref}: EXISTS (type: {unit['type']})")
    else:
        print(f"❌ {ref}: NOT FOUND")

# Show all units starting with 45638.80
parking_units = [u for u in units if u['unit_number'].startswith('45638.80')]
print(f"\nUnits 45638.80.xxx: {len(parking_units)}")
for u in parking_units[:10]:
    print(f"  - {u['unit_number']}: {u['type']}")


