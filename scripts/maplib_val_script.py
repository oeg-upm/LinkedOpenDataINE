import argparse
import sys
import os
import maplib
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="High-performance SHACL validation using maplib.")
    
    # Define CLI Arguments
    parser.add_argument("data", help="Path to the local RDF data file (e.g., data.ttl)")
    parser.add_argument("shapes", help="Path to the SHACL shapes file (e.g., shapes.ttl)")
    parser.add_argument("-o", "--output", default="report.ttl", help="Path to save the validation report")

    args = parser.parse_args()

    # 1. Initialize the Model
    m = maplib.Model()
    sh = maplib.Model()
    
    try:
        # 1. Convert the CLI strings into absolute Path objects
        data_path_obj = Path(args.data).resolve()
        shapes_path_obj = Path(args.shapes).resolve()

        # 2. Convert those objects into proper file:// URIs
        # This handles the 'file:' scheme and fixes slashes automatically
        data_uri = data_path_obj.as_uri()
        shapes_uri = shapes_path_obj.as_uri()
        # 2. Correct Method per Documentation: m.read()
        # This loads the RDF content into the model's internal graph
        print(f"--- Loading Data: {args.data} ---")
        m.read(args.data)
        
        print(f"--- Loading Shapes: {args.shapes} ---")
        sh.read(args.shapes)

        # 3. Run Validation
        # maplib.Model.validate() assumes shapes are already in the graph 
        print("--- Running Validation ---")
        report = m.validate(shape_graph=args.shapes)  

        if report.conforms():
            print("✅ Success: Data conforms to shapes.")
        else:
            print("❌ Failure: Data is invalid.")
            print(f"--- Writing Report to {args.output} ---")
            
            # 4. Access the report graph and write it
            # The ValidationReport object has a 'graph' property
            report.graph.write(args.output)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()