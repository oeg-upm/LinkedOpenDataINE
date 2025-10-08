import csv
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os
import sys
import morph_kgc
import time

import rdflib

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
            ine_var, dim = line.strip().split(',')
            var_list.append((ine_var, dim))
    return var_list

#Earlier version of the code, a new version has been added that automatically generates the DCAT metadata.
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
    g_mappings.add((predicate_object_map_bnode, RR.predicate, DCT.publisher))
    g_mappings.add((predicate_object_map_bnode, RR.object, URIRef("https://www.ine.es/")))
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

# Method for adding the INE specific metadata. 
def add_INE_metadata(file_path):
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        dataset_uri = INELOD[file_name]
        triples_map_dataset = INELOD[file_name + "_TriplesMapDataset"]
        # Add logical source for the dataset
        logical_source_bnode = BNode()
        g_mappings.add((triples_map_dataset, RML.logicalSource, logical_source_bnode))
        g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
        g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))

        # Add subject map for the dataset
        subject_map_bnode = BNode()
        g_mappings.add((triples_map_dataset, RR.subjectMap, subject_map_bnode))
        g_mappings.add((subject_map_bnode, RR.constant, dataset_uri))
        g_mappings.add((subject_map_bnode, RR["class"], QB.DataSet)) 

        # Helper to add a predicate-object mapping
        def add_pom(pred, obj, lang=None):
            pom_bnode = BNode()
            g_mappings.add((triples_map_dataset, RR.predicateObjectMap, pom_bnode))
            g_mappings.add((pom_bnode, RR.predicate, pred))
            if lang:
                g_mappings.add((pom_bnode, RR.object, Literal(obj, lang=lang)))
            else:
                g_mappings.add((pom_bnode, RR.object, obj if isinstance(obj, URIRef) else Literal(obj)))

        # Add required triples
        add_pom(RDFS.label, file_name)
        add_pom(DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/"))
        add_pom(DCT.source, URIRef(f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}"))
        add_pom(RDF.type, DCAT.Dataset)
        add_pom(DCT.identifier, Literal(f"urn:ine:es:TABLA:TPX:{file_name}", lang="es"))
        add_pom(DCT.language, URIRef("http://publications.europa.eu/resource/authority/language/SPA"))
        add_pom(DCAT.contactPoint, URIRef("https://www.ine.es/"))
        add_pom(DCT.publisher,URIRef("https://www.ine.es/"))
        add_pom(QB.structure, INELOD[file_name + "_dsd"])

        # Add dcat:distribution blank nodes for each distribution
        distributions = [
            {
                "type": DCAT.Distribution,
                "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
                "title": [("Html", "es"), ("Html", "en")],
                "format": URIRef("http://publications.europa.eu/resource/authority/file-type/HTML"),
                "mediaType": URIRef("http://www.iana.org/assignments/media-types/text/html"),
                "applicableLegislation": URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"),
                "license": URIRef("https://www.ine.es/aviso_legal"),
            },
            {
                "type": DCAT.Distribution,
                "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
                "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/px/{file_name}.px?nocab=1",
                "title": [("PC-Axis", "es"), ("PC-Axis", "en")],
                "applicableLegislation": URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"),
                "license": URIRef("https://www.ine.es/aviso_legal"),
            },
            {
                "type": DCAT.Distribution,
                "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
                "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/xlsx/{file_name}.xlsx?nocab=1",
                "title": [("Excel: Extensión XLSX", "es"), ("Excel: XLSX extension", "en")],
                "format": URIRef("http://publications.europa.eu/resource/authority/file-type/XLSX"),
                "mediaType": URIRef("http://www.iana.org/assignments/media-types/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                "applicableLegislation": URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"),
                "license": URIRef("https://www.ine.es/aviso_legal"),
            },
            {
                "type": DCAT.Distribution,
                "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
                "downloadURL": f"https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/{file_name}",
                "title": [("Json", "es"), ("Json", "en")],
                "format": URIRef("http://publications.europa.eu/resource/authority/file-type/JSON"),
                "mediaType": URIRef("http://www.iana.org/assignments/media-types/application/json"),
                "applicableLegislation": URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"),
                "license": URIRef("https://www.ine.es/aviso_legal"),
            },
            {
                "type": DCAT.Distribution,
                "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
                "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/csv_bd/{file_name}.csv?nocab=1",
                "title": [("CSV: separado por tabuladores", "es"), ("CSV: Tab Separated", "en")],
                "format": URIRef("http://publications.europa.eu/resource/authority/file-type/CSV"),
                "mediaType": URIRef("http://www.iana.org/assignments/media-types/text/csv"),
                "applicableLegislation": URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"),
                "license": URIRef("https://www.ine.es/aviso_legal"),
            },
            {
                "type": DCAT.Distribution,
                "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
                "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{file_name}.csv?nocab=1",
                "title": [("CSV: separado por ;", "es"), ("CSV: Separated by ;", "en")],
                "format": URIRef("http://publications.europa.eu/resource/authority/file-type/CSV"),
                "mediaType": URIRef("http://www.iana.org/assignments/media-types/text/csv"),
                "applicableLegislation": URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"),
                "license": URIRef("https://www.ine.es/aviso_legal"),
            },
        ]
        order = 1
        for dist in distributions:
            triples_map_uri_dist = INELOD[file_name] + "_dist"+str(order)
            dist_bnode = BNode()
            pom_bnode = BNode()
            g_mappings.add((triples_map_dataset, RR.predicateObjectMap, pom_bnode))
            g_mappings.add((pom_bnode, RR.predicate, DCAT.distribution))
            g_mappings.add((pom_bnode, RR.objectMap, dist_bnode))
            g_mappings.add((dist_bnode, RR.parentTriplesMap, triples_map_uri_dist))
            logical_source_bnode = BNode()
            g_mappings.add((triples_map_uri_dist, RML.logicalSource, logical_source_bnode))
            g_mappings.add((logical_source_bnode, RML.source, Literal(file_path)))
            g_mappings.add((logical_source_bnode, RML.referenceFormulation, QL.CSV))
            subject_map_bnode = BNode()
            g_mappings.add((triples_map_uri_dist, RR.subjectMap, subject_map_bnode))
            g_mappings.add((subject_map_bnode, RR.constant, BNode()))
            g_mappings.add((subject_map_bnode, RR.termType, RR.BlankNode))
            # Distribution type
            dist_pom_bnode = BNode()
            g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))
            g_mappings.add((dist_pom_bnode, RR.predicate, RDF.type))
            g_mappings.add((dist_pom_bnode, RR.object, dist["type"]))
            # accessURL
            if "accessURL" in dist:            
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))            
                g_mappings.add((dist_pom_bnode, RR.predicate, DCAT.accessURL))
                g_mappings.add((dist_pom_bnode, RR.object, URIRef(dist["accessURL"])))
            # downloadURL
            if "downloadURL" in dist:
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))             
                g_mappings.add((dist_pom_bnode, RR.predicate, DCAT.downloadURL))
                g_mappings.add((dist_pom_bnode, RR.object, URIRef(dist["downloadURL"])))
            # Titles (multilingual)
            for t, lang in dist["title"]:
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))
                g_mappings.add((dist_pom_bnode, RR.predicate,DCT.title))
                g_mappings.add((dist_pom_bnode, RR.object, Literal(t, lang=lang)))
            # Format (constant, if present)
            if "format" in dist:
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))
                g_mappings.add((dist_pom_bnode, RR.predicate, DCT["format"]))
                g_mappings.add((dist_pom_bnode, RR.object, dist["format"]))
            # MediaType (constant, if present)
            if "mediaType" in dist:
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))
                g_mappings.add((dist_pom_bnode, RR.predicate, DCAT.mediaType))
                g_mappings.add((dist_pom_bnode, RR.object, dist["mediaType"]))
            # applicableLegislation (constant)
            if "applicableLegislation" in dist:
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))
                g_mappings.add((dist_pom_bnode, RR.predicate, DCAT.applicableLegislation))
                g_mappings.add((dist_pom_bnode, RR.object, dist["applicableLegislation"]))
            if "license" in dist:
            # license (constant)
                dist_pom_bnode = BNode()
                g_mappings.add((triples_map_uri_dist, RR.predicateObjectMap, dist_pom_bnode))
                g_mappings.add((dist_pom_bnode, RR.predicate, DCT.license))
                g_mappings.add((dist_pom_bnode, RR.object, dist["license"]))
            order += 1


def add_POM_from_csv(file_path):
    #variables = load_variables("dimensiones_correspondence.txt")
    ontology = Graph().parse("vocabularios/inelod-voc-auto.ttl", format="turtle")
    measu_list = load_variables("lista_medidas.txt")
    measures = load_variables("medidas_correspondence.txt")
    measures_set = set(measu for measu, _ in measures)
    medidas_set = set(ine_var for ine_var, _ in measu_list)
    #variables_dict = dict(variables)
    measures_dict = dict(measures)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    dsd_uri = INELOD[file_name + "_dsd"]
    detect_and_replace_measures(file_path)

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

    triples_map_obs = INELOD[file_name + "_Observations"]
    multiple_measures = False

    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        columns = reader.fieldnames
        order = 1
        for column in columns:
            # Dimension columns
            # First we check if the column is in the vocabulary of the dimensions.
            ask_query = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
                    f' ASK {{ ?s rdfs:label <{column}> .}}'
            res = ontology.query(ask_query)
            if res.askAnswer and column not in medidas_set and column not in measures_dict:
                select_query = f' PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' \
                                f' SELECT ?s WHERE {{ ?s rdfs:label <{column}> .}}'
                for result in ontology.query(select_query):
                    dim = result["s"]
                print(f"Processing column: {column} as dimension with URI: {dim}")
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
                g_mappings.add((predicate_object_map_bnode, RR.object, URIRef(dim.strip())))
                predicate_object_map_bnode = BNode()
                g_mappings.add((triples_map_uri_dim, RR.predicateObjectMap, predicate_object_map_bnode))
                g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.order))
                g_mappings.add((predicate_object_map_bnode, RR.object, Literal(order)))
                component_bnode = BNode()
                predicate_object_map_bnode = BNode()
                g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_dim))
                pom_bnode = BNode()
                g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                g_mappings.add((pom_bnode, RR.predicate, URIRef(dim.strip())))
                object_bnode = BNode()
                g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                g_mappings.add((object_bnode, RML.reference, Literal(column)))
                order += 1
                continue

            # Single measure column (Total)
            if column == "Total" and not multiple_measures:
                print(f"Processing column: {column}")
                triples_map_uri_measu = triples_map_dsd + "_measu"
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
                g_mappings.add((predicate_object_map_bnode, RR.object, SDMX_MEASURE.obsValue))
                component_bnode = BNode()
                predicate_object_map_bnode = BNode()
                g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_measu))
                pom_bnode = BNode()
                g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                g_mappings.add((pom_bnode, RR.predicate, SDMX_MEASURE.obsValue))
                object_bnode = BNode()
                g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                g_mappings.add((object_bnode, RML.reference, Literal(column)))
                g_mappings.add((object_bnode, RR.datatype, XSD.float))
                multiple_measures = True
                continue

            # Individual measure columns
            if column in measures_dict:
                rdf_measure = measures_dict[column]
                print(f"Processing column: {column}")
                triples_map_uri_measu = triples_map_dsd + "_measu"
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
                g_mappings.add((predicate_object_map_bnode, RR.object, URIRef(rdf_measure)))
                component_bnode = BNode()
                predicate_object_map_bnode = BNode()
                g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_measu))
                pom_bnode = BNode()
                g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                g_mappings.add((pom_bnode, RR.predicate, URIRef(rdf_measure)))
                object_bnode = BNode()
                g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                g_mappings.add((object_bnode, RML.reference, Literal(column)))
                g_mappings.add((object_bnode, RR.datatype, XSD.float))
                continue

            # Multiple measures (measureType)
            if column in medidas_set:
                print(f"Processing column: {column} as multiple measures")
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
                g_mappings.add((predicate_object_map_bnode, RR.object, QB.measureType))
                predicate_object_map_bnode = BNode()
                g_mappings.add((triples_map_uri_dim, RR.predicateObjectMap, predicate_object_map_bnode))
                g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.order))
                g_mappings.add((predicate_object_map_bnode, RR.object, Literal(order)))
                component_bnode = BNode()
                predicate_object_map_bnode = BNode()
                g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_dim))
                pom_bnode = BNode()
                g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                g_mappings.add((pom_bnode, RR.predicate, QB.measureType))
                object_bnode = BNode()
                g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                g_mappings.add((object_bnode, RML.reference, Literal(column)))
                pom_bnode = BNode()
                g_mappings.add((triples_map_obs, RR.predicateObjectMap, pom_bnode))
                predicate_bnode = BNode()
                g_mappings.add((pom_bnode, RR.predicateMap, predicate_bnode))
                g_mappings.add((predicate_bnode, RML.reference, Literal(column)))
                object_bnode = BNode()
                g_mappings.add((pom_bnode, RR.objectMap, object_bnode))
                if len(sys.argv) > 2 and sys.argv[2]:
                    g_mappings.add((object_bnode, RML.reference, Literal(sys.argv[2])))
                else:
                    g_mappings.add((object_bnode, RML.reference, Literal("Total")))
                g_mappings.add((object_bnode, RR.datatype, XSD.float))
                order += 1
                measu_order = 1
                for measure_group, measure in measu_list:
                    if column == measure_group:
                        print(f"Processing measure group: {measure_group} with measure: {measure}")
                        triples_map_uri_measu = triples_map_dsd + "_measu" + str(measu_order)
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
                        g_mappings.add((predicate_object_map_bnode, RR.object, URIRef(measure)))
                        component_bnode = BNode()
                        predicate_object_map_bnode = BNode()
                        g_mappings.add((triples_map_dsd, RR.predicateObjectMap, predicate_object_map_bnode))
                        g_mappings.add((predicate_object_map_bnode, RR.predicate, QB.component))
                        g_mappings.add((predicate_object_map_bnode, RR.objectMap, component_bnode))
                        g_mappings.add((component_bnode, RR.parentTriplesMap, triples_map_uri_measu))
                        measu_order += 1

# Function to detect and replace measures in the CSV file
def detect_and_replace_measures(file_path):
    # Load lista_medidas.txt as a list of tuples (first element is the one to look for)
    medidas = rdflib.Graph().parse("rdf_vocabularies/inelod-voc-auto.ttl", format="ttl")
    
    # Get the measurement argument if provided
    measurement = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Measurement to append: {measurement}")
    with open(file_path, mode='r', encoding='utf-8', errors='replace') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        headers = next(reader, None)
        if headers is None:
            return False

        # Replace "Total" column name with measurement if provided
        if measurement and "Total" in headers:
            headers = [measurement if h == "Total" else h for h in headers]
        # SPARQL query to find ine:MeasureSet matching CSV columns

        csv_columns_set = set(headers)
        query = """
            PREFIX ine: <http://stats.linkeddata.es/voc/cubes/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label
            WHERE {
                ?set a ine:MeasureSet ;
                    rdfs:label ?label .
            }
            GROUP BY ?label
        """
        matching_set = None
        for row in medidas.query(query):
                measure_labels = set(row["labels"].split(","))
                if measure_labels.issubset(csv_columns_set):
                        matching_set = row["set"]
                        matching_column = next((h for h in headers if h == row["label"]), None)
                        print(f"Found matching MeasureSet: {matching_set} for columns: {measure_labels}")
                        # If Measure Set column exists, append sys.argv[2] to its header only
                        # Find the index of the matching column and append measurement to its header
                        matching_idx = headers.index(matching_column) if matching_column in headers else None
                        if matching_idx is not None and measurement:
                            headers[matching_idx] = f"{headers[matching_idx]} {sys.argv[2]}"
                        # Read all rows, ensuring UTF-8 encoding
                        rows = [[cell.encode('utf-8', 'replace').decode('utf-8') for cell in row] for row in reader]
                        # Also append measurement to each cell in the "Unidad" and/or "Tipo de dato" column
                        for row in rows:
                            if measurement:
                                if unidad_idx is not None and len(row) > unidad_idx:
                                    row[unidad_idx] = f"{row[unidad_idx]} {measurement}"
                                if tipo_dato_idx is not None and len(row) > tipo_dato_idx:
                                    row[tipo_dato_idx] = f"{row[tipo_dato_idx]} {measurement}"
                else:
                    # If there is not any MeasureSet, just read the rows
                    rows = [[cell.encode('utf-8', 'replace').decode('utf-8') for cell in row] for row in reader]

        # Find indices of headers that are in medidas_set
        medidas_indices = [i for i, header in enumerate(headers) if header in medidas_set]
        if not medidas_indices:
            # Write back headers and rows if only header changes were made
            with open(file_path, mode='w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(headers)
                writer.writerows(rows)
            return False

        # Replace values in measure columns
        updated_rows = []
        for row in rows:
            for idx in medidas_indices:
                cell_value = row[idx]
                if cell_value in measures_dict:
                    row[idx] = measures_dict[cell_value]
            updated_rows.append(row)

    # Write the updated rows back to the file
    with open(file_path, mode='w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(headers)
        writer.writerows(updated_rows)
    print(f"CSV updated with replaced measures and column names.")
    return True

# Function to add an index column to the CSV file and strip non-UTF-8 characters
def csv_add_index(file_path):
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
#add_template_metadata(csv_file_path)
add_INE_metadata(csv_file_path)
print(f"Template metadata added in {time.time() - start_time:.2f} seconds")

# Add index column to the CSV file
start_time = time.time()
csv_add_index(csv_file_path)
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