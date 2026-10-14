"""
NORA-style iterative reasoning simulation using Apache Spark and Cassandra.
Rule: rdfs:subClassOf transitivity
  If (A subClassOf B) and (B subClassOf C) then (A subClassOf C)
"""
import os
import time
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from cassandra.cluster import Cluster

CASSANDRA_HOST = "127.0.0.1"
KEYSPACE = "nora"
TABLE = "triples"
MAX_ITER = 5
RESULTS_DIR = "results"
RDFS_SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"

os.makedirs(RESULTS_DIR, exist_ok=True)

# ------------------------------------------------------------
# 1. Spark session with Cassandra connector
# ------------------------------------------------------------
spark = (
    SparkSession.builder
    .appName("NORA_Simulation")
    .master("local[*]")
    .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1")
    .config("spark.cassandra.connection.host", CASSANDRA_HOST)
    .config("spark.sql.extensions", "com.datastax.spark.connector.CassandraSparkExtensions")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)

print("Spark session created.")

# ------------------------------------------------------------
# 2. Connect to Cassandra for writes
# ------------------------------------------------------------
cluster = Cluster([CASSANDRA_HOST])
session = cluster.connect(KEYSPACE)
insert_stmt = session.prepare(f"""
    INSERT INTO {TABLE} (subject, predicate, object)
    VALUES (?, ?, ?)
""")

# ------------------------------------------------------------
# 3. Iterative reasoning
# ------------------------------------------------------------
iteration_data = []

for iteration in range(1, MAX_ITER + 1):
    t0 = time.perf_counter()

    # Read all triples from Cassandra into Spark DataFrame
    df = (
        spark.read
        .format("org.apache.spark.sql.cassandra")
        .options(table=TABLE, keyspace=KEYSPACE)
        .load()
    )

    # Extract subClassOf triples
    sub_df = df.filter(col("predicate") == RDFS_SUBCLASS).select(
        col("subject").alias("a"),
        col("object").alias("b")
    )

    # Join on b == a to find transitive pairs: (A subClassOf B), (B subClassOf C) -> (A subClassOf C)
    sub_df2 = sub_df.select(
        col("a").alias("b2"),
        col("b").alias("c")
    )

    inferred = (
        sub_df.join(sub_df2, sub_df["b"] == sub_df2["b2"])
        .select(
            col("a").alias("subject"),
            col("c").alias("object")
        )
        .distinct()
    )

    inferred = inferred.withColumn("predicate", col("object").cast("string"))
    inferred = inferred.withColumn("predicate", 
        __import__("pyspark.sql.functions", fromlist=["lit"]).lit(RDFS_SUBCLASS))

    inferred = inferred.select("subject", "predicate", "object")

    new_count = inferred.count()
    t1 = time.perf_counter()
    elapsed = t1 - t0

    print(f"Iteration {iteration}: {new_count} inferred triples, {elapsed:.3f}s")
    iteration_data.append({
        "iteration": iteration,
        "inferred_triples": new_count,
        "time_seconds": round(elapsed, 3)
    })

    if new_count == 0:
        print("No new triples. Reasoning converged.")
        break

    # Write inferred triples back to Cassandra
    rows = inferred.collect()
    for row in rows:
        session.execute(insert_stmt, (row["subject"], row["predicate"], row["object"]))

# ------------------------------------------------------------
# 4. Save results
# ------------------------------------------------------------
df_results = pd.DataFrame(iteration_data)
df_results.to_csv(f"{RESULTS_DIR}/iteration_times.csv", index=False)
print(f"\nResults saved to {RESULTS_DIR}/iteration_times.csv")
print(df_results.to_string(index=False))

spark.stop()
cluster.shutdown()