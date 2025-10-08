from rdflib import Graph
import sys

def transform_rdf_to_ntriples(input_file, output_file):
    # Create a graph
    g = Graph()
    
    # Parse the input RDF file
    g.parse(input_file, format='turtle')
    
    # Serialize the graph to N-Triples format
    g.serialize(destination=output_file, format='nt')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python format_transformation.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    transform_rdf_to_ntriples(input_file, output_file)