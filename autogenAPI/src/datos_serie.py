from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os

from src.prefixes import *
from src.utils import *
from src.dimensions_measure import getSeriesDimensions, getMeausure


def generate_DATOSSERIE_mappings(url, seriesCOD, parameters, measure_ontology_file, dimension_ontology_file):
    g_mappings = Graph()

    for prefix, namespace in namespaces.items():
        g_mappings.bind(prefix, namespace)
    
    measure = getMeausure(seriesCOD, measure_ontology_file)
    dimensions = getSeriesDimensions(seriesCOD, dimension_ontology_file)

    logical_sources_map = {
        "LS_Root": "$",
        "LS_Data": "$.Data.*"
    }

    if "M" in parameters.get("tip"):
        logical_sources_map["LS_Meta"] = "$.MetaData.*"

    add_logical_sources(logical_sources_map, seriesCOD, url, parameters, g_mappings)
    _add_static_template(seriesCOD, url, g_mappings)
    _add_slice_dsd(seriesCOD, dimensions, measure, g_mappings)

    _add_series_triplesmap(seriesCOD, dimensions, measure, parameters, g_mappings)
    if parameters.get("det") == "2" or parameters.get("det") == "1":
        _add_unidad_triplesmap(seriesCOD, parameters, g_mappings)
        _add_scale_triplesmap(seriesCOD, parameters, g_mappings)

    _add_observations_triplesmap(seriesCOD, measure, parameters, g_mappings)
    if parameters.get("det") == "2":
        _add_tipodato_triplesmap(seriesCOD, parameters, g_mappings)
        _add_periodo_triplesmap(seriesCOD, parameters, g_mappings)

    if "M" in parameters.get("tip"):
        _add_meta_triplesmap(seriesCOD, parameters, g_mappings)
        if parameters.get("det") == 2:
            _add_variable_triplesmap(seriesCOD, parameters, g_mappings)

    return g_mappings

def _add_slice_dsd(inputId, dimensions, measure,g_mappings):
    dsd = INELOD[inputId + "TriplesMap_DSD"]
    g_mappings.add((dsd, RDF.type, RML.TriplesMap))
    g_mappings.add((dsd, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(dsd, QB.DataStructureDefinition, g_mappings, constant_uri=INELOD[inputId + "SliceKey_DSD"])

    for dimension_pred, dimension_obj in dimensions.items():
        add_pom_obj(dsd, QB.dimension, dimension_pred, g_mappings)
    add_pom_obj(dsd, QB.measure, measure, g_mappings)
    add_pom_obj(dsd, QB["sliceKey"], INELOD[inputId+ "_SliceKey"], g_mappings)

def _add_static_template(inputId, urlAPI, g_mappings):
    dataset_static = INELOD[inputId + "_TriplesMap_SliceKey"]
    g_mappings.add((dataset_static, RDF.type, RML.TriplesMap))
    g_mappings.add((dataset_static, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(dataset_static, QB.sliceKey, g_mappings, constant_uri=INELOD[inputId+ "_SliceKey"])

    add_pom_obj(dataset_static, DCT.title, inputId , g_mappings, lang="es")
    add_pom_obj(dataset_static, DCAT.distribution, INELOD[inputId + "-dist"], g_mappings)

    add_pom_ref(dataset_static, EX["nota"], "texto", g_mappings)

    distribution_static = INELOD["Distribution_Static"]
    g_mappings.add((distribution_static, RDF.type, RML.TriplesMap))
    g_mappings.add((distribution_static, RML.logicalSource, INELOD["LS_Root"]))
    add_subject_map(distribution_static, DCAT.Distribution, g_mappings, constant_uri=INELOD[inputId + "-dist"])
    #add_pom_obj(distribution_static, DCT.format, FORMATS.JSON)
    add_pom_obj(distribution_static, DCAT.accessURL, URIRef(urlAPI), g_mappings)


def _add_series_triplesmap(inputId, dimensions, measure, parameters, g_mappings):
    series = INELOD[inputId + "_Series"]
    g_mappings.add((series, RDF.type, RML.TriplesMap))
    g_mappings.add((series, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(series, QB["slice"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "series/{COD}")

    add_pom_ref(series, EX["codigo"], "COD", g_mappings)
    add_pom_ref(series, RDFS.label, "Nombre", g_mappings)

    add_pom_obj(series, QB.measure, measure, g_mappings)
    add_pom_obj(series, QB["SliceStructure"], INELOD[inputId + "_SliceKey"], g_mappings)

    for dimension_pred, dimension_obj in dimensions.items():
        add_pom_obj(series, dimension_pred, dimension_obj, g_mappings)

    if parameters.get("det") == "2" or parameters.get("det") == "1":
        add_pom_parenttpm(series, EX["hasScale"], INELOD[inputId + "_Escala"], "Escala.Id", "Escala.Id", g_mappings)
        add_pom_parenttpm(series, EX["hasUnit"], INELOD[inputId + "_Unidad"], "Unidad.Id", "Unidad.Id", g_mappings)
    else:
        if "A" not in parameters.get("tip"):        
            add_pom_ref(series, EX["hasScale"], "Escala.Id", g_mappings)
            add_pom_ref(series, EX["hasUnit"], "Unidad.Id", g_mappings)
        else:
            add_pom_ref(series, EX["hasScale"], "Escala.Nombre", g_mappings)
            add_pom_ref(series, EX["hasUnit"], "Unidad.Nombre", g_mappings)

    if "M" in parameters.get("tip"):
        add_pom_parenttpm(series, EX["metadataComp"], INELOD[inputId + "_Meta"], "MetaData.Id", "Id", g_mappings)

def _add_unidad_triplesmap(inputId, parameters, g_mappings):
    unidad = INELOD[inputId + "_Unidad"]
    g_mappings.add((unidad, RDF.type, RML.TriplesMap))
    g_mappings.add((unidad, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(unidad, QB["AttributeProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "unit/{Unidad.Id}")

    add_pom_ref(unidad, RDFS.label, "Unidad.Nombre", g_mappings)
    if "A" not in parameters.get("tip"):
        add_pom_ref(unidad, EX["id"], "Unidad.Id", g_mappings, datatype=XSD.integer)
    add_pom_ref(unidad, EX["codigo"], "Unidad.Codigo", g_mappings)

def _add_scale_triplesmap(inputId, parameters, g_mappings):
    escala = INELOD[inputId + "_Escala"]
    g_mappings.add((escala, RDF.type, RML.TriplesMap))
    g_mappings.add((escala, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(escala, QB["AttributeProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" +  "scale/{Escala.Id}")

    add_pom_ref(escala, RDFS.label, "Escala.Nombre", g_mappings)
    if "A" not in parameters.get("tip"):
        add_pom_ref(escala, EX["id"], "Escala.Id", g_mappings, datatype=XSD.integer)
    add_pom_ref(escala, EX["codigo"], "Escala.Codigo", g_mappings)
    add_pom_ref(escala, EX["factor"], "Escala.Factor", g_mappings)


def _add_observations_triplesmap(inputId, measure, parameters, g_mappings):
    observation = INELOD[inputId + "_Observations"]
    g_mappings.add((observation, RDF.type, RML.TriplesMap))
    g_mappings.add((observation, RML.logicalSource, INELOD["LS_Data"]))

    add_subject_map(observation, QB.Observation, g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "obs/" + inputId + "_{CodigoPeriodo}")

    add_pom_obj(observation, QB.dataSet, INELOD[inputId], g_mappings)
    add_pom_obj(observation, QB.observationGroup, URIRef("https://stats.linkeddata.es/voc/cubes/" + "series/" + inputId), g_mappings)

    add_pom_ref(observation, SDMX_DIMENSION.year, "Anyo", g_mappings, datatype=XSD.gYear)
    add_pom_ref(observation, SDMX_DIMENSION.date, "Fecha", g_mappings, datatype=XSD.long)
    add_pom_ref(observation, measure, "Valor", g_mappings, datatype=XSD.float)

    if "A" not in parameters.get("tip"): 
        if parameters.get("det") == "2":
            add_pom_ref(observation, SDMX_DIMENSION.refPeriod, "CodigoPeriodo", g_mappings)
            add_pom_ref(observation, SDMX_DIMENSION.refPeriod, "NombrePeriodo", g_mappings)
        add_pom_ref(observation, EX["secret"], "Secreto", datatype=XSD.boolean, g_mappings=g_mappings) 

    if parameters.get("det") == "2":
        add_pom_parenttpm(observation, EX.tipoDato, INELOD[inputId + "_TipoDato"], "TipoDato.Id", "Id", g_mappings)
        add_pom_parenttpm(observation, EX.periodo, INELOD[inputId + "_Periodo"], "Periodo.Id", "Id", g_mappings)
    else:
        if "A" not in parameters.get("tip"):
            add_pom_ref(observation, EX["tipoDato"], "TipoDato.Id", g_mappings)
            add_pom_ref(observation, EX["periodo"], "Periodo.Id", g_mappings)
        else:
            add_pom_ref(observation, EX["tipoDato"], "TipoDato.Nombre", g_mappings)
            add_pom_ref(observation, EX["periodo"], "Periodo.Nombre", g_mappings)

def _add_tipodato_triplesmap(inputId, parameters, g_mappings):
    tipoDato = INELOD[inputId + "_TipoDato"]
    g_mappings.add((tipoDato, RDF.type, RML.TriplesMap))
    g_mappings.add((tipoDato, RML.logicalSource, INELOD["LS_Data"]))

    add_subject_map(tipoDato, QB["AttributeProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "tipodato/{TipoDato.Id}")

    add_pom_ref(tipoDato, RDFS.label, "TipoDato.Nombre", g_mappings)
    add_pom_ref(tipoDato, EX.codigoTipoDato, "TipoDato.Codigo", g_mappings)
    if "A" not in parameters.get("tip"):
        add_pom_ref(tipoDato, EX.id, "TipoDato.Id", g_mappings, datatype=XSD.integer)

def _add_periodo_triplesmap(inputId, parameters, g_mappings):
    periodo = INELOD[inputId + "_Periodo"]
    g_mappings.add((periodo, RDF.type, RML.TriplesMap))
    g_mappings.add((periodo, RML.logicalSource, INELOD["LS_Data"]))

    add_subject_map(periodo, QB["DimensionProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "periodo/{Periodo.Id}")

    if "A" not in parameters.get("tip"):
        add_pom_ref(periodo, EX.id, "Periodo.Id", g_mappings, datatype=XSD.integer)
        add_pom_ref(periodo, RDFS.label, "Periodo.Nombre_largo", g_mappings)
        add_pom_ref(periodo, EX["mesInicio"], "Periodo.Mes_Inicio", g_mappings)
        add_pom_ref(periodo, EX["diaInicio"], "Periodo.Dia_Inicio", g_mappings)
        add_pom_ref(periodo, SDMX_MEASURE.obsValue, "Periodo.Valor", g_mappings)
        add_pom_ref(periodo, INE["periodicity"], "Periodo.FK_Periodicidad", g_mappings)

    add_pom_ref(periodo, RDFS.comment, "Periodo.Nombre", g_mappings)
    add_pom_ref(periodo, EX.codigo, "Periodo.Codigo", g_mappings)

def _add_meta_triplesmap(inputId, parameters, g_mappings):
    metadata = INELOD[inputId + "_Meta"]
    g_mappings.add((metadata, RDF.type, RML.TriplesMap))
    g_mappings.add((metadata, RML.logicalSource, INELOD["LS_Meta"]))

    add_subject_map(metadata, EX["MetadataItem"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "md/{Id}")

    add_pom_ref(metadata, EX["id"], "Id", g_mappings, datatype=XSD.integer)
    add_pom_ref(metadata, EX["nombre"], "Nombre", g_mappings)
    add_pom_ref(metadata, EX["codigo"], "Codigo", g_mappings)
    add_pom_ref(metadata, EX["nota"], "Nota", g_mappings)

    if parameters.get("det") == 2:
        add_pom_parenttpm(metadata, EX["variable"], INELOD[inputId + "_Variable"], "Variable.Id", "Variable.Id", g_mappings)
    else:
        add_pom_ref(metadata, EX["variable"], "Variable.Id", g_mappings)

def _add_variable_triplesmap(inputId, parameters, g_mappings):
    variable = INELOD[inputId + "_Variable"]
    g_mappings.add((variable, RDF.type, RML.TriplesMap))
    g_mappings.add((variable, RML.logicalSource, INELOD["LS_Meta"]))

    add_subject_map(variable, QB["concept"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "variable/{Variable.Id}")

    add_pom_ref(variable, RDFS.label, "Variable.Nombre", g_mappings)
    add_pom_ref(variable, EX["id"], "Variable.Id", g_mappings, datatype=XSD.integer)
    add_pom_ref(variable, EX["codigo"], "Variable.Codigo", g_mappings)