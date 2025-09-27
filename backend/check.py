import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print(f"Attempting to connect to Neo4j...")
print(f"URI: {uri}")
print(f"User: {user}")
print(f"Password: {password}")
print("-" * 20)

try:
    # Create a driver instance
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # This is the key test. It verifies the connection and routing.
    driver.verify_connectivity()
    
    print("✅ Connection successful!")
    
    # Optional: Run a simple query
    with driver.session() as session:
        result = session.run("RETURN 'Hello, Neo4j!' AS message;")
        record = result.single()
        print(f"Query result: {record['message']}")

except Exception as e:
    print(f"❌ Failed to connect to Neo4j.")
    print(f"Error: {e}")

finally:
    if 'driver' in locals() and driver:
        driver.close()
        print("Driver closed.")