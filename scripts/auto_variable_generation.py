import os
"""
Author: Diego Conde Herreros
This script is designed to automate the process of adding variable definitions to an RDF vocabulary file. 
It uses the `rdflib` library to handle RDF data and provides functionality to load variable correspondences 
from a text file and add new terms to an RDF vocabulary in Turtle format.
How the code works:
1. The script defines a namespace (`INELod`) for the RDF vocabulary.
2. It includes a function `load_variable_correspondence` to read a text file containing variable names and their corresponding URIs.
    - The file should have each line formatted as: `variable_name,variable_uri`.
3. The `add_term_to_vocabulary` function checks if a term is already present in the RDF vocabulary.
    - If not, it adds the term as an RDF class with a label and a comment.
    - The updated RDF vocabulary is saved back to the file.
4. The `main` function prompts the user to input a variable name, checks if it exists in the correspondence file, 
    and adds it to the RDF vocabulary if applicable.
How to use:
1. Prepare a text file (`variables_correspondence.txt`) containing variable names and their URIs, separated by commas.
2. Ensure you have an RDF vocabulary file (`inelod-voc.ttl`) or let the script create one if it doesn't exist.
3. Run the script and input the variable name when prompted.
4. The script will add the variable to the RDF vocabulary if it is not already present.
Dependencies:
- Python 3.x
- `rdflib` library for RDF handling
Note:
- Update the `variables_file` and `rdf_vocabulary_file` paths as needed to match your file locations.
- Ensure the RDF vocabulary file is in Turtle format for compatibility.
"""
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from transformers import pipeline



# Paths to the files
variables_file = "variables_correspondence.txt"
rdf_vocabulary_file = "inelod-voc.ttl"

# Namespace for the RDF vocabulary
INELod = Namespace("https://stats.linkeddata.es/voc/cubes/vocabulary#")

# Function to load a list of tuples from a txt file
def load_variables(file_path):
    var_list = []
    with open(file_path, mode='r', encoding='utf-8') as txtfile:
        for line in txtfile:
            # Assuming each line in the txt file is a tuple in the form (subject, predicate, object)
            ine_var, sdmx_dim = line.strip().split(',')
            var_list.append((ine_var, sdmx_dim))
    return var_list

def add_term_to_vocabulary(variable_name, variable_uri, rdf_file):
    """Add a term definition to the RDF vocabulary if not present."""
    g = Graph()

    # Load existing RDF vocabulary if it exists
    if os.path.exists(rdf_file):
        g.parse(rdf_file, format="turtle")

    # Check if the term is already in the vocabulary
    term_uri = URIRef(variable_uri)
    if (term_uri, None, None) in g:
        print(f"The term '{variable_name}' is already in the RDF vocabulary.")
        return

    # Load a pre-trained language model for text generation
    generator = pipeline("text-generation", model="gpt-2")

    # Generate a comment for the variable
    auto_comment_prompt = f"Generate a descriptive comment for the variable in a statistical domain context.'{variable_name}':"
    auto_comment = generator(auto_comment_prompt, max_length=50, num_return_sequences=1)[0]['generated_text']
    print(auto_comment)
    # Generate a dimension property for the variable
    auto_dimension_prompt = f"A dimension property is being created, please infer which of the dimensions available at https://raw.githubusercontent.com/UKGovLD/publishing-statistical-data/master/specs/src/main/vocab/sdmx-dimension.ttl would be suited as a superproperty of:'{variable_name}':"
    auto_dimension = generator(auto_dimension_prompt, max_length=50, num_return_sequences=1)[0]['generated_text']
    print(auto_dimension)
    
    # Add the term to the RDF vocabuterm_urilary
    g.add((variable_uri, RDF.type, RDF.Property))
    g.add((variable_uri, RDF.type, QB.DimensionProperty))
    g.add((term_uri, RDFS.label, Literal(variable_name)))
    g.add((term_uri, RDFS.comment, auto_comment))
    g.add((term_uri, RDFS.subPropertyOf,auto_dimension))
    g.add((term_uri, RDFS.range, RDFS.Resource))

    # Save the updated RDF vocabulary
    g.serialize(rdf_file, format="turtle")
    print(f"Added term '{variable_name}' to the RDF vocabulary.")


def process_variable(variable_name, variables_file_path, rdf_vocabulary_file_path):
    """Process a variable by adding it to the RDF vocabulary if applicable."""
    # Load variable correspondence
    correspondence = load_variables(variables_file_path)
    if variable_name in correspondence:
        print(f"Variable '{variable_name}' found in {variables_file_path}.")
        return
    else:
        # Normalize the variable name
        variable_name[0].lower()
        variable_name.strip().replace(" ", "")
        variable_uri = INELod[variable_name]
        # Add the term to the RDF vocabulary
        add_term_to_vocabulary(variable_name, variable_uri, rdf_vocabulary_file_path)
