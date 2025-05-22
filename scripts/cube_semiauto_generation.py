import csv
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os
import sys
import morph_kgc
import time

# Define namespaces for the data used in the RDF cubes.
EX = Namespace("http://example.org/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
SCHEMA = Namespace("http://schema.org/")
RR = Namespace("http://www.w3.org/ns/r2rml#")
RML = Namespace("http://semweb.mmlab.be/ns/rml#")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")
TRANSIT = Namespace("http://vocab.org/transit/terms/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
WGS84_POS = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
INELOD = Namespace("http://stats.linkeddata.es/voc/cubes/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VOID = Namespace("http://rdfs.org/ns/void#")
DCT = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
ORG = Namespace("http://www.w3.org/ns/org#")
ADMINGEO = Namespace("http://data.ordnancesurvey.co.uk/ontology/admingeo/")
INTERVAL = Namespace("http://reference.data.gov.uk/def/intervals/")
QB = Namespace("http://purl.org/linked-data/cube#")
SDMX_CONCEPT = Namespace("http://purl.org/linked-data/sdmx/2009/concept#")
SDMX_DIMENSION = Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
SDMX_ATTRIBUTE = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
SDMX_MEASURE = Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
SDMX_METADATA = Namespace("http://purl.org/linked-data/sdmx/2009/metadata#")
SDMX_CODE = Namespace("http://purl.org/linked-data/sdmx/2009/code#")
SDMX_SUBJECT = Namespace("http://purl.org/linked-data/sdmx/2009/subject#")
INELOD_VOC = Namespace("http://stats.linkeddata.es/voc/cubes/vocabulary/")

# Create two new graphs, one for the data and one for the RML mappings for the observations
g_mappings = Graph()
namespaces = {
    "ex": EX, "schema": SCHEMA, "rr": RR, "rml": RML, "ql": QL, "transit": TRANSIT, "xsd": XSD, 
    "wgs84_pos": WGS84_POS, "inelod": INELOD, "rdf": RDF, "rdfs": RDFS, "owl": OWL, "skos": SKOS, 
    "void": VOID, "dct": DCT, "foaf": FOAF, "org": ORG, "admingeo": ADMINGEO, "interval": INTERVAL, 
    "qb": QB, "sdmx-concept": SDMX_CONCEPT, "sdmx-dimension": SDMX_DIMENSION, "sdmx-attribute": SDMX_ATTRIBUTE, 
    "sdmx-measure": SDMX_MEASURE, "sdmx-metadata": SDMX_METADATA, "sdmx-code": SDMX_CODE, "sdmx-subject": SDMX_SUBJECT, "inelod-voc" : INELOD_VOC
}
for prefix, namespace in namespaces.items():
    g_mappings.bind(prefix, namespace)

# Function to load a list of tuples from a txt file
def load_variables(file_path):
    var_list = []
    with open(file_path, mode='r', encoding='utf-8') as txtfile:
        for line in txtfile:
            # Assuming each line in the txt file is a tuple in the form (subject, predicate, object)
            ine_var, sdmx_dim = line.strip().split(',')
            var_list.append((ine_var, sdmx_dim))
    return var_list

# Function to add template metadata to the data graph, those terms that cannot be inferred automatically are left as XXXX values.
def add_template_metadata(file_path):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    triples_map_dataset = INELOD[file_name + "_TriplesMapDataset"]
    g_mappings.add((triples_map_dataset, RDF.type, RR.TriplesMap))
    logical_source_bnode = BNode()
    g_mappings.add((triples_map_dataset, RML.logicalSource, logical_source_bnode))
    g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
    g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))
    subject_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.subjectMap, subject_map_bnode))
    g_mappings.add((subject_map_bnode, RR.constant, INELOD[file_name]))
    g_mappings.add((subject_map_bnode, RR["class"], QB.DataSet))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCT.title))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, RDFS.label))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCT.description))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCT.publisher))
    g_mappings.add((predicate_object_map_bnode, RR.object, URIRef("https://www.ine.es/")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCT.license))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCT.source))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate,  DCT.created))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate,   DCT.modified))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate,   DCT.issued))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCAT.theme))
    g_mappings.add((predicate_object_map_bnode, RR.object, Literal("XXXX")))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.structure))
    g_mappings.add((predicate_object_map_bnode, RR.object, INELOD[file_name + "_dsd"]))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_dataset, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, SDMX_ATTRIBUTE.unitMeasure))
    g_mappings.add((predicate_object_map_bnode, RR.object, SDMX_MEASURE.obsValue))

def add_POM_from_csv(file_path):
    variables = load_variables("variables_correspondence.txt")
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    dsd_uri = INELOD[file_name + "_dsd"]
    #TM Definition corresponding to the dimensions
    triples_map_dsd = INELOD[file_name + "_TriplesMapDSD"]
    g_mappings.add((triples_map_dsd, RDF.type, RR.TriplesMap))
    logical_source_bnode = BNode()
    g_mappings.add((triples_map_dsd, RML.logicalSource, logical_source_bnode))
    g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
    g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))
    subject_map_bnode = BNode()
    g_mappings.add((triples_map_dsd, RR.subjectMap, subject_map_bnode))
    g_mappings.add((subject_map_bnode, RR.constant, dsd_uri))
    g_mappings.add((subject_map_bnode, RR["class"], QB.DataStructureDefinition))
    #Triples map for the observations
    triples_map_obs = INELOD[file_name + "_Observations"]
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        columns = reader.fieldnames
        order = 1
        for column in columns:
            #print("Entro en el for")
            #print(column)
            for ine_var, sdmx_dim in variables:
                if column == ine_var and column != "Total":
                    #print("Entro en el if")
                    #This part of the mappings corresponds to the blank nodes of each of the dimensions
                    triples_map_uri_dim = triples_map_dsd + "_bndim" + str(order)
                    g_mappings.add((triples_map_uri_dim, RDF.type, RR.TriplesMap))
                    logical_source_bnode = BNode()
                    g_mappings.add((triples_map_uri_dim, RML.logicalSource, logical_source_bnode))
                    g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
                    g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))
                    subject_map_bnode = BNode()
                    g_mappings.add((triples_map_uri_dim, RR.subjectMap, subject_map_bnode))
                    g_mappings.add((subject_map_bnode, RR.constant, BNode()))
                    g_mappings.add((subject_map_bnode, RR.termType, RR.BlankNode))                                    
                    predicate_object_map_bnode = BNode()
                    g_mappings.add((triples_map_uri_dim, RR.predicateObjectMap, predicate_object_map_bnode))
                    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.dimension))
                    g_mappings.add((predicate_object_map_bnode, RR.object, URIRef(sdmx_dim.strip())))
                    predicate_object_map_bnode = BNode()
                    g_mappings.add((triples_map_uri_dim, RR.predicateObjectMap, predicate_object_map_bnode))
                    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.order))
                    g_mappings.add((predicate_object_map_bnode, RR.object, Literal(order)))
                    #This is the part that corresponds to the components of the DSD.
                    component_bnode = BNode()
                    predicate_object_map_bnode = BNode()
                    g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                    g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                    g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_dim))
                    #Part that includes the POM for the observations
                    order += 1
                    pom_bnode = BNode()
                    g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                    g_mappings.add((pom_bnode, RR.predicate, URIRef(sdmx_dim.strip())))
                    object_bnode = BNode()
                    g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                    g_mappings.add((object_bnode, RML.reference, Literal(column)))

                elif column == ine_var and column == "Total":
                    triples_map_uri_measu = triples_map_dsd+"_measu"
                    g_mappings.add((triples_map_uri_measu, RDF.type, RR.TriplesMap))
                    logical_source_bnode = BNode()
                    g_mappings.add((triples_map_uri_measu, RML.logicalSource, logical_source_bnode))
                    g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
                    g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))
                    subject_map_bnode = BNode()
                    g_mappings.add((triples_map_uri_measu, RR.subjectMap, subject_map_bnode))
                    g_mappings.add((subject_map_bnode, RR.constant, BNode()))
                    g_mappings.add((subject_map_bnode, RR.termType, RR.BlankNode))                                    
                    predicate_object_map_bnode = BNode()
                    g_mappings.add((triples_map_uri_measu, RR.predicateObjectMap, predicate_object_map_bnode))
                    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.measure))
                    g_mappings.add((predicate_object_map_bnode, RR.object, URIRef(sdmx_dim.strip())))
                    #This is the part that corresponds to the components of the DSD.
                    component_bnode = BNode()
                    predicate_object_map_bnode = BNode()
                    g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                    g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                    g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_measu))
                    #Part that includes the POM for the observations
                    pom_bnode = BNode()
                    g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                    g_mappings.add((pom_bnode, RR.predicate, URIRef(sdmx_dim)))
                    object_bnode = BNode()
                    g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                    g_mappings.add((object_bnode, RML.reference, Literal(column)))
                    g_mappings.add((object_bnode, RR.datatype, XSD.int))

# Function to add an index column to the CSV file and strip non-UTF-8 characters
def add_index_column(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8', errors='replace') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            headers = next(reader, None)
            if headers is None:
                print("CSV file is empty or improperly formatted")
                return
            headers = [header.lstrip('\ufeff') for header in headers]  # Strip BOM if present
            if "index" in headers:
                print("Index column already exists in the CSV file")
                return
            rows = [[cell.encode('utf-8', 'replace').decode('utf-8') for cell in row] for row in reader]
        # Add the index column to the headers
        headers.insert(0, "index")
        # Add the index to each row
        indexed_rows = [[str(index)] + row for index, row in enumerate(rows, start=1)]
        # Write the updated CSV back to the file 
        with open(file_path, mode='w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(headers)
            writer.writerows(indexed_rows)
    except Exception as e:
        print(f"An error occurred while processing the CSV file: {e}")

def add_mappings_from_csv(file_path):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    triples_map_obs = INELOD[file_name + "_Observations"]
    g_mappings.add((triples_map_obs, RDF.type, RR.TriplesMap))
    logical_source_bnode = BNode()
    g_mappings.add((triples_map_obs, RML.logicalSource, logical_source_bnode))
    g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
    g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))
    subject_map_bnode = BNode()
    g_mappings.add((triples_map_obs, RR.subjectMap, subject_map_bnode))
    g_mappings.add((subject_map_bnode, RR.template, Literal("https://stats.linkeddata.es/voc/cubes/" + file_name + "/o{index}")))
    g_mappings.add((subject_map_bnode, RR['class'], QB.Observation))
    predicate_object_map_bnode = BNode()
    g_mappings.add((triples_map_obs, RR.predicateObjectMap, predicate_object_map_bnode))
    g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.dataSet))
    g_mappings.add((predicate_object_map_bnode, RR.object, INELOD[file_name]))

# Main execution of the python script
# Path to the CSV file
csv_file_path = sys.argv[1]

# Add template metadata to the data graph
start_time = time.time()
add_template_metadata(csv_file_path)
print(f"Template metadata added in {time.time() - start_time:.2f} seconds")

# Add index column to the CSV file
start_time = time.time()
add_index_column(csv_file_path)
print(f"Index column added in {time.time() - start_time:.2f} seconds")

# Add the DSD to the graph.
start_time = time.time()
add_POM_from_csv(csv_file_path)
print(f"POM added in {time.time() - start_time:.2f} seconds")

# Create the mappings for the observations.
start_time = time.time()
add_mappings_from_csv(csv_file_path)
print(f"Mappings created in {time.time() - start_time:.2f} seconds")

# Serialize the mappings graph to a file in Turtle format
start_time = time.time()
g_mappings.serialize(format='turtle', destination="auto_mappings.ttl")
print(f"Mappings serialized in {time.time() - start_time:.2f} seconds")

# Execution of Morph-KGC to materialize the data.
start_time = time.time()

os.system(f"python -m morph_kgc ../configuration/config_CSV.ini")
os.rename("knowledge-graph.nt", f"{os.path.splitext(os.path.basename(csv_file_path))[0]}.nt")
os.rename("auto_mappings.ttl", f"auto_mappings{os.path.splitext(os.path.basename(csv_file_path))[0]}.ttl")
print(f"Data materialized in {time.time() - start_time:.2f} seconds")