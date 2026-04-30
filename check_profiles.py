import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='crembo_db_new'
)

cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT id, title, description, is_visible, order_index FROM organization_profiles ORDER BY order_index')
rows = cursor.fetchall()

print(f'Total profiles in database: {len(rows)}')
for r in rows:
    print(f'  - ID: {r["id"]}')
    print(f'    Title: {r["title"]}')
    print(f'    Description: {r["description"][:50]}...' if r["description"] else '    Description: (empty)')
    print(f'    Visible: {bool(r["is_visible"])}')
    print(f'    Order: {r["order_index"]}')
    print()

conn.close()
