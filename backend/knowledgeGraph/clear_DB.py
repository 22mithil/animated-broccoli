from neo4j import GraphDatabase

# Connection settings
uri = "neo4j+s://934bb46e.databases.neo4j.io" # or your Neo4j URI
user = "934bb46e"
password = "zbI5ka8n4RdbPsmPr2rMJrKPwTtIZ7AMKpGqtbXMM44"

driver = GraphDatabase.driver(uri, auth=(user, password))

def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")

with driver.session() as session:
    session.execute_write(clear_database)

driver.close()
print("✅ All nodes and relationships have been deleted.")
