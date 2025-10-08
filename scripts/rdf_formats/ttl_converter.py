from rdflib import Graph

# Load the N-Triples file
input_file = "data_cubes/data/cap_66615.nt"     # Replace with your actual N-Triples file path
output_file = "data_cubes/data/cap_66615.ttl"  # Replace with your desired Turtle file path

# Create an RDF graph
g = Graph()

# Parse the N-Triples file
g.parse(input_file, format="nt")

# Serialize the graph to Turtle format
g.serialize(destination=output_file, format="turtle")

print(f"Converted to Turtle format.")
