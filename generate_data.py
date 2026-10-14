"""
Generate synthetic RDF triples mimicking LUBM structure.
"""
import csv
import random
import os

random.seed(42)

UNIVERSITY = "http://www.University0.edu"
DEPARTMENTS = [f"{UNIVERSITY}/Department{i}" for i in range(1, 6)]
PROFESSORS = [f"{UNIVERSITY}/Professor{i}" for i in range(1, 21)]
STUDENTS = [f"{UNIVERSITY}/Student{i}" for i in range(1, 101)]
COURSES = [f"{UNIVERSITY}/Course{i}" for i in range(1, 31)]

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"

triples = []

# 1. Class hierarchy (subClassOf)
class_hierarchy = [
    ("Professor", "Faculty"),
    ("Student", "Person"),
    ("Faculty", "Person"),
    ("Department", "Organization"),
    ("University", "Organization"),
    ("Course", "AcademicItem"),
]

for sub, sup in class_hierarchy:
    triples.append((f"http://www.University0.edu/{sub}", RDFS_SUBCLASS, f"http://www.University0.edu/{sup}"))

# 2. Additional subClassOf chain for transitivity
triples.append(("http://www.University0.edu/Faculty", RDFS_SUBCLASS, "http://www.University0.edu/Employee"))
triples.append(("http://www.University0.edu/Employee", RDFS_SUBCLASS, "http://www.University0.edu/Agent"))

# 3. Instances (rdf:type)
for prof in PROFESSORS:
    triples.append((prof, RDF_TYPE, "http://www.University0.edu/Professor"))

for stud in STUDENTS:
    triples.append((stud, RDF_TYPE, "http://www.University0.edu/Student"))

for dept in DEPARTMENTS:
    triples.append((dept, RDF_TYPE, "http://www.University0.edu/Department"))

for course in COURSES:
    triples.append((course, RDF_TYPE, "http://www.University0.edu/Course"))

triples.append((UNIVERSITY, RDF_TYPE, "http://www.University0.edu/University"))

# 4. Add random noise triples to reach ~10k
predicates = [
    "http://www.University0.edu/worksFor",
    "http://www.University0.edu/memberOf",
    "http://www.University0.edu/teaches",
    "http://www.University0.edu/takesCourse",
]

entities = PROFESSORS + STUDENTS + DEPARTMENTS + COURSES
while len(triples) < 10000:
    s = random.choice(entities)
    p = random.choice(predicates)
    o = random.choice(entities)
    triples.append((s, p, o))

os.makedirs("data", exist_ok=True)
with open("data/lubm_triples.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["subject", "predicate", "object"])
    writer.writerows(triples)

print(f"Generated {len(triples)} triples -> data/lubm_triples.csv")