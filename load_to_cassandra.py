"""
Load RDF triples from CSV into Cassandra.
"""
import csv
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

CASSANDRA_HOST = "127.0.0.1"
KEYSPACE = "nora"
TABLE = "triples"

def main():
    # Connect
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect()

    # Create keyspace
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)
    session.set_keyspace(KEYSPACE)

    # Create table
    session.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            subject text,
            predicate text,
            object text,
            PRIMARY KEY ((subject), predicate, object)
        )
    """)

    # Load CSV
    insert_stmt = session.prepare(f"""
        INSERT INTO {TABLE} (subject, predicate, object)
        VALUES (?, ?, ?)
    """)

    count = 0
    with open("data/lubm_triples.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            session.execute(insert_stmt, (row["subject"], row["predicate"], row["object"]))
            count += 1

    print(f"Inserted {count} triples into Cassandra keyspace '{KEYSPACE}'.")
    cluster.shutdown()

if __name__ == "__main__":
    main()