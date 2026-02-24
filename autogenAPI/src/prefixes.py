from rdflib import Graph, URIRef, Literal, Namespace, BNode

# Define namespaces for the data used in the RDF cubes.
EX = Namespace("http://example.com/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
SCHEMA = Namespace("http://schema.org/")
RR = Namespace("http://www.w3.org/ns/r2rml#")
RML = Namespace("http://w3id.org/rml/")
QL = Namespace("http://semweb.mmlab.be/ns/ql#")
TRANSIT = Namespace("http://vocab.org/transit/terms/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
WGS84_POS = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
INELOD = Namespace("http://stats.linkeddata.es/voc/cubes/")
INE = Namespace("https://stats.linkeddata.es/voc/cubes/vocabulary#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VOID = Namespace("http://rdfs.org/ns/void#")
DCT = Namespace("http://purl.org/dc/terms/")
FORMATS = Namespace("https://www.w3.org/ns/formats/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
ORG = Namespace("http://www.w3.org/ns/org#")
HTV = Namespace("http://www.w3.org/2011/http#")
ADMINGEO = Namespace("http://data.ordnancesurvey.co.uk/dimensions/admingeo/")
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

namespaces = {
    "ex": EX, "schema": SCHEMA, "rr": RR, "rml": RML, "ql": QL, "transit": TRANSIT, "xsd": XSD,
    "wgs84_pos": WGS84_POS, "inelod": INELOD, "rdf": RDF, "rdfs": RDFS, "owl": OWL, "skos": SKOS,
    "void": VOID, "dct": DCT, "foaf": FOAF, "org": ORG, "admingeo": ADMINGEO, "interval": INTERVAL,
    "qb": QB, "sdmx-concept": SDMX_CONCEPT, "sdmx-dimension": SDMX_DIMENSION, "sdmx-attribute": SDMX_ATTRIBUTE,
    "sdmx-measure": SDMX_MEASURE, "sdmx-metadata": SDMX_METADATA, "sdmx-code": SDMX_CODE, "sdmx-subject": SDMX_SUBJECT, "inelod-voc" : INELOD_VOC, "htv": HTV,
    "formats": FORMATS, "dcat": DCAT, "ine": INE
}
