"""
Diagnostic script to check label storage in database
"""
import psycopg2
import json
from pprint import pprint

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="autoimmune_db",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

# Get a sample record with labels
query = """
SELECT 
    record_id,
    import_batch_id,
    dataset_type,
    data
FROM flexible_dataset_wide
WHERE data IS NOT NULL
LIMIT 5;
"""

cur.execute(query)
records = cur.fetchall()

print("=== SAMPLE RECORDS ===\n")
for i, (record_id, batch_id, dataset_type, data) in enumerate(records, 1):
    print(f"\nRecord {i}:")
    print(f"  Record ID: {record_id}")
    print(f"  Batch ID: {batch_id}")
    print(f"  Dataset Type: {dataset_type}")
    print(f"  Data structure:")
    
    # Pretty print the JSONB data
    if data:
        # Check for labels
        if 'labels_disease_severity' in data:
            print(f"    ✓ Found labels_disease_severity: {data['labels_disease_severity']}")
        else:
            print(f"    ✗ No labels_disease_severity found")
        
        # Check for labeling metadata
        if '_labeling_metadata' in data:
            print(f"    ✓ Found _labeling_metadata:")
            pprint(data['_labeling_metadata'], indent=6)
        else:
            print(f"    ✗ No _labeling_metadata found")
        
        # Show all top-level keys
        print(f"    All top-level keys ({len(data)} keys):")
        for key in sorted(data.keys())[:20]:  # Show first 20
            if key.startswith('_labeling'):
                print(f"      - {key}: {data[key]}")

# Get batch IDs
print("\n\n=== AVAILABLE BATCHES ===\n")
cur.execute("""
SELECT 
    import_batch_id,
    COUNT(*) as record_count,
    dataset_type,
    MIN(created_at) as first_import,
    MAX(created_at) as last_import
FROM flexible_dataset_wide
GROUP BY import_batch_id, dataset_type
ORDER BY MAX(created_at) DESC;
""")

batches = cur.fetchall()
for batch_id, count, dtype, first, last in batches:
    print(f"Batch: {batch_id}")
    print(f"  Type: {dtype}")
    print(f"  Records: {count}")
    print(f"  Imported: {first} to {last}")
    
    # Check how many have labels
    cur.execute("""
    SELECT COUNT(*) 
    FROM flexible_dataset_wide 
    WHERE import_batch_id = %s 
    AND data ? 'labels_disease_severity';
    """, (batch_id,))
    labeled_count = cur.fetchone()[0]
    print(f"  With labels_disease_severity: {labeled_count}")
    print()

cur.close()
conn.close()

print("\n=== DIAGNOSIS COMPLETE ===")
