from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os

from src.prefixes import *
from src.utils import *
from src.dimensions_measure import getTableDimensions, getOperationsDimensions

def generate_DATOS_METADATAOPERACION_mappings(url, operacion, parameters, measure_ontology_file, dimension_ontology_file):
    g_mappings = Graph()

    for prefix, namespace in namespaces.items():
        g_mappings.bind(prefix, namespace)
    dimensions = getOperationsDimensions(operacion, dimension_ontology_file)

    logical_sources_map = {
        "LS_Root": "$.*",
        "LS_Data": "$.*"
    }
    if "M" in parameters.get("tip"):
        logical_sources_map["LS_Meta"] = "$.*.MetaData.*"
    if parameters.get("det") == "2" or parameters.get("det") == "1":
        logical_sources_map["LS_Escala"] = "$.*.Escala"
    logical_sources_map["LS_Unidad"] = "$.*.Unidad"

    param_strings = [f"{k}{v}" for k, v in sorted(parameters.items())]
    param_strings = "_".join(param_strings)
    operacion = f"{operacion}_{param_strings}"

    add_logical_sources(logical_sources_map, operacion, url, parameters, g_mappings)
    _add_static_template(operacion, url, parameters, g_mappings)
    add_dataStructureDefinition(dimensions, operacion, g_mappings)
    add_slice_key(operacion, dimensions, g_mappings)

    _add_series_triplesmap(operacion, dimensions, parameters, g_mappings)
    if parameters.get("det") == "2" or parameters.get("det") == "1":
        _add_unidad_triplesmap(operacion, parameters, g_mappings)
        _add_scale_triplesmap(operacion, parameters, g_mappings)

    _add_observations_triplesmap(operacion, parameters, g_mappings)
    if parameters.get("det") == "2":
        _add_tipodato_triplesmap(operacion, parameters, g_mappings)
        _add_periodo_triplesmap(operacion, parameters, g_mappings)

    if "M" in parameters.get("tip"):
        _add_meta_triplesmap(operacion, parameters, g_mappings)
        if parameters.get("det") == 2:
            _add_variable_triplesmap(operacion, parameters, g_mappings)

    return g_mappings

def generate_DATOSTABLA_mappings(url, tableId, parameters, measure_ontology_file, dimension_ontology_file):
    g_mappings = Graph()

    for prefix, namespace in namespaces.items():
        g_mappings.bind(prefix, namespace)
    dimensions = getTableDimensions(tableId, dimension_ontology_file)

    logical_sources_map = {
        "LS_Root": "$.*",
        "LS_Data": "$.*",
        "LS_Notas": "$..Notas[*]"
    }
    if "M" in parameters.get("tip"):
        logical_sources_map["LS_Meta"] = "$.*.MetaData.*"
    if parameters.get("det") == "2" or parameters.get("det") == "1":
        logical_sources_map["LS_Escala"] = "$.*.Escala"
    logical_sources_map["LS_Unidad"] = "$.*.Unidad"

    param_strings = [f"{k}{v}" for k, v in sorted(parameters.items())]
    param_strings = "_".join(param_strings)
    tableId = f"{tableId}_{param_strings}"

    add_logical_sources(logical_sources_map, tableId, url, parameters, g_mappings)
    _add_static_template(tableId, url, parameters, g_mappings)
    add_dataStructureDefinition(dimensions, tableId, g_mappings)
    add_slice_key(tableId, dimensions, g_mappings)

    _add_series_triplesmap(tableId, dimensions, parameters, g_mappings)
    if parameters.get("det") == "2" or parameters.get("det") == "1":
        _add_unidad_triplesmap(tableId, parameters, g_mappings)
        _add_scale_triplesmap(tableId, parameters, g_mappings)

    _add_observations_triplesmap(tableId, parameters, g_mappings)
    if parameters.get("det") == "2":
        _add_tipodato_triplesmap(tableId, parameters, g_mappings)
        _add_periodo_triplesmap(tableId, parameters, g_mappings)

    if "M" in parameters.get("tip"):
        _add_meta_triplesmap(tableId, parameters, g_mappings)
        if parameters.get("det") == 2:
            _add_variable_triplesmap(tableId, parameters, g_mappings)

    return g_mappings

def add_slice_key(inputId, dimensions, g_mappings, source=INELOD["LS_Unidad"]):
    sliceKeyTP = INELOD["SliceKey_TriplesMap"]
    g_mappings.add((sliceKeyTP, RDF.type, RML.TriplesMap))
    g_mappings.add((sliceKeyTP, RML.logicalSource, source))

    add_subject_map(sliceKeyTP, QB["SliceKey"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "slice_key/{Id}")
    add_pom_obj(sliceKeyTP, RDFS.label, "Slice by Series", g_mappings)
    add_pom_obj(sliceKeyTP, RDFS.comment, "Slice by fixing every dimension except period", g_mappings)

    for dimension, _ in dimensions.items():
        add_pom_obj(sliceKeyTP, QB["componentProperty"], dimension, g_mappings)

    slice_dsd = INELOD["SliceKey_DSD_TriplesMap"]
    g_mappings.add((slice_dsd, RDF.type, RML.TriplesMap))
    g_mappings.add((slice_dsd, RML.logicalSource, INELOD["LS_Unidad"]))

    add_subject_map(slice_dsd, QB.DataStructureDefinition, g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "slice_dsd/{Id}")
    add_pom_parenttpm(slice_dsd, QB["sliceKey"], sliceKeyTP, "Id", "Id", g_mappings)
    


def add_dataStructureDefinition(dimensions, inputId, g_mappings):
    dataStructureDefinitionTP = INELOD[f"{inputId}_TriplesMapDSD"]
    g_mappings.add((dataStructureDefinitionTP, RDF.type, RML.TriplesMap))
    g_mappings.add((dataStructureDefinitionTP, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(dataStructureDefinitionTP, QB.DataStructureDefinition, g_mappings, constant_uri=INELOD[f"{inputId}_dsd"])

    def _add_component_dsd(inputId, dimension, order, g_mappings):
        componentTP = INELOD[f"{inputId}_TriplesMapDSD_bndim{order}"]
        g_mappings.add((componentTP, RDF.Type, RML.TriplesMap))
        g_mappings.add((componentTP, RML.logicalSource, INELOD["LS_Root"]))
        add_pom_obj(componentTP, QB.order, order, g_mappings)
        add_pom_obj(componentTP, QB.dimension, dimension, g_mappings)
        add_subject_map_BN(componentTP, g_mappings)
        return componentTP
    
    order = 1
    for dimension, _ in dimensions.items():
        add_pom_parenttpm(dataStructureDefinitionTP, QB.component, _add_component_dsd(inputId, dimension, order, g_mappings), None, None, g_mappings)
        order += 1
    add_pom_parenttpm(dataStructureDefinitionTP, QB.component, _add_component_dsd(inputId, SDMX_DIMENSION["refPeriod"], order, g_mappings), None, None, g_mappings)


def _add_static_template(table_name, urlAPI, parameters, g_mappings):
    dataset_static = INELOD["DataSet_Static"]
    g_mappings.add((dataset_static, RDF.type, RML.TriplesMap))
    g_mappings.add((dataset_static, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(dataset_static, QB.Dataset, g_mappings, constant_uri=INELOD[table_name])

    add_pom_obj(dataset_static, DCT.title, table_name, g_mappings, lang="es")
    add_pom_obj(dataset_static, QB.structure, INELOD[table_name + "_dsd"], g_mappings)

    add_pom_obj(dataset_static, DCT.source, URIRef(urlAPI), g_mappings)
    add_pom_obj(dataset_static, DCT.publisher, INE["INE"], g_mappings)
    add_pom_obj(dataset_static, DCT.license, URIRef("https://creativecommons.org/licenses/by/4.0/"), g_mappings)
    add_pom_obj(dataset_static, DCT.identifier, Literal(f"urn:ine:es:TABLA:{table_name}"), g_mappings)
    add_pom_obj(dataset_static, DCT.language, URIRef("http://publications.europa.eu/resource/authority/language/SPA"), g_mappings)

def _add_series_triplesmap(table_name, dimensions, parameters, g_mappings):
    series = INELOD[table_name + "_Series"]
    g_mappings.add((series, RDF.type, RML.TriplesMap))
    g_mappings.add((series, RML.logicalSource, INELOD["LS_Root"]))

    add_subject_map(series, QB["slice"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" +  "series/{COD}")

    add_pom_ref(series, EX["codigo"], "COD", g_mappings)
    add_pom_ref(series, RDFS.label, "Nombre", g_mappings)
    add_pom_parenttpm(series, QB.sliceStructure, INELOD["SliceKey_TriplesMap"], "Unidad.Id", "Id", g_mappings)

    for dimension_pred, dimension_id in dimensions.items():
        add_pom_ref(series, dimension_pred, "MetaData[?(@.Variable.Id==" + str(dimension_id) + ")].Nombre", g_mappings)

    add_pom_ref(series, QB["measure"], "Unidad.Nombre", g_mappings)

    if (parameters.get("det") == "2" or parameters.get("det") == "1"):
        add_pom_parenttpm(series, EX["hasScale"], INELOD[table_name + "_Escala"], "Escala.Id", "Id", g_mappings)
        add_pom_parenttpm(series, EX["hasUnit"], INELOD[table_name + "_Unidad"], "Unidad.Id", "Id", g_mappings)
    else:
        if "A" not in parameters.get("tip"):
            add_pom_ref(series, EX["hasScale"], "Escala.Id", g_mappings)
            add_pom_ref(series, EX["hasUnit"], "Unidad.Id", g_mappings)
        else:
            add_pom_ref(series, EX["hasScale"], "Escala.Nombre", g_mappings)
            add_pom_ref(series, EX["hasUnit"], "Unidad.Nombre", g_mappings)

    if "M" in parameters.get("tip"):
        add_pom_parenttpm(series, EX["metadataComp"], INELOD[table_name + "_Meta"], "MetaData.Id", "Id", g_mappings)

def _add_observations_triplesmap(table_name, parameters, g_mappings):
    observations = INELOD[table_name + "_Observations"]
    g_mappings.add((observations, RDF.type, RML.TriplesMap))
    g_mappings.add((observations, RML.logicalSource, INELOD["LS_Data"]))

    add_subject_map(observations, QB.Observation, g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "obs/{COD}_{Data.CodigoPeriodo}")
    add_pom_obj(observations, QB.Dataset, INELOD[table_name], g_mappings)

    add_pom_parenttpm(observations, QB.slice, INELOD[table_name + "_Series"], "COD", "COD", g_mappings)
    
    if "A" not in parameters.get("tip"): 
        if parameters.get("det") == "2":
            add_pom_ref(observations, SDMX_DIMENSION.refPeriod, "Data.CodigoPeriodo", g_mappings)
            add_pom_ref(observations, SDMX_DIMENSION.refPeriod, "Data.NombrePeriodo", g_mappings)
        add_pom_ref(observations, EX["secret"], "Data.Secreto", datatype=XSD.boolean, g_mappings=g_mappings) 

    add_pom_ref(observations, SDMX_DIMENSION.year, "Data.Anyo", datatype=XSD.gYear, g_mappings=g_mappings)
    add_pom_ref(observations, SDMX_DIMENSION.date, "Data.Fecha", datatype=XSD.long, g_mappings=g_mappings)
    add_pom_ref(observations, SDMX_MEASURE.obsValue, "Data.Valor", datatype=XSD.float, g_mappings=g_mappings)

    if parameters.get("det") == "2":
        add_pom_parenttpm(observations, EX["tipoDato"], INELOD[table_name + "_TipoDato"], "Data.TipoDato.Id", "Data.TipoDato.Id", g_mappings)
        add_pom_parenttpm(observations, EX["periodo"], INELOD[table_name + "_Periodo"], "Data.Periodo.Id", "Data.Periodo.Id", g_mappings)
    else:
        if "A" not in parameters.get("tip"):
            add_pom_ref(observations, EX["tipoDato"], "Data.TipoDato.Id", g_mappings)
            add_pom_ref(observations, EX["periodo"], "Data.Periodo.Id", g_mappings)
        else:
            add_pom_ref(observations, EX["tipoDato"], "Data.TipoDato.Nombre", g_mappings)
            add_pom_ref(observations, EX["periodo"], "Data.Periodo.Nombre", g_mappings)

def _add_unidad_triplesmap(table_name, parameters, g_mappings):
    units = INELOD[table_name + "_Unidad"]
    g_mappings.add((units, RDF.type, RML.TriplesMap))
    g_mappings.add((units, RML.logicalSource, INELOD["LS_Unidad"]))

    add_subject_map(units, QB["MeasureProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "unit/{Id}")

    add_pom_ref(units, INE["unitOfMeasurement"], "Nombre", g_mappings)
    if "A" not in parameters.get("tip"):
        add_pom_ref(units, RDFS.label, "Id", g_mappings)


def _add_scale_triplesmap(table_name, parameters, g_mappings):
    scale = INELOD[table_name + "_Escala"]
    g_mappings.add((scale, RDF.type, RML.TriplesMap))
    g_mappings.add((scale, RML.logicalSource, INELOD["LS_Escala"]))

    add_subject_map(scale, QB["AttributeProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "scale/{Id}")

    add_pom_ref(scale, RDFS.label, "Nombre", g_mappings)
    add_pom_ref(scale, EX["factor"], "Factor", g_mappings)
    if "A" not in parameters.get("tip"):
        add_pom_ref(scale, EX["id"], "Id", datatype=XSD.integer, g_mappings=g_mappings)

def _add_tipodato_triplesmap(table_name, parameters, g_mappings):
    tipo_dato = INELOD[table_name + "_TipoDato"]
    g_mappings.add((tipo_dato, RDF.type, RML.TriplesMap))
    g_mappings.add((tipo_dato, RML.logicalSource, INELOD["LS_Data"]))

    add_subject_map(tipo_dato, QB["AttributeProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "tipodato/{Data.TipoDato.Id}")

    add_pom_ref(tipo_dato, RDFS.label, "Data.TipoDato.Nombre", g_mappings)
    add_pom_ref(tipo_dato, EX["codigo"], "Data.TipoDato.Codigo", g_mappings)
    if "A" not in parameters.get("tip"):
        add_pom_ref(tipo_dato, EX["id"], "Data.TipoDato.Id", g_mappings, datatype=XSD.integer)

def _add_periodo_triplesmap(table_name, parameters, g_mappings):
    periodo = INELOD[table_name + "_Periodo"]
    g_mappings.add((periodo, RDF.type, RML.TriplesMap))
    g_mappings.add((periodo, RML.logicalSource, INELOD["LS_Data"]))

    add_subject_map(periodo, QB["DimensionProperty"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "period/{Data.Periodo.Id}")

    add_pom_ref(periodo, RDFS.comment, "Data.Periodo.Nombre", g_mappings)
    add_pom_ref(periodo, EX["codigo"], "Data.Periodo.Codigo", g_mappings)

    if "A" not in parameters.get("tip"):
        add_pom_ref(periodo, RDFS.label, "Data.Periodo.Nombre_largo", g_mappings)
        add_pom_ref(periodo, EX["mesInicio"], "Data.Periodo.Mes_inicio", g_mappings)
        add_pom_ref(periodo, EX["diaInicio"], "Data.Periodo.Dia_inicio", g_mappings)
        add_pom_ref(periodo, EX["id"], "Data.Periodo.Id", g_mappings, datatype=XSD.integer)
        add_pom_ref(periodo, EX["value"], "Data.Periodo.Valor", g_mappings)
        add_pom_ref(periodo, INE.periodicity, "Data.Periodo.FK_Periodicidad", g_mappings)

def _add_meta_triplesmap(table_name, parameters, g_mappings):
    meta = INELOD[table_name + "_Meta"]
    g_mappings.add((meta, RDF.type, RML.TriplesMap))
    g_mappings.add((meta, RML.logicalSource, INELOD["LS_Meta"]))

    add_subject_map(meta, EX["MetadataItem"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "md/{Id}")

    add_pom_ref(meta, EX["mdId"], "Id", g_mappings, datatype=XSD.integer)
    add_pom_ref(meta, EX["mdNombre"], "Nombre", g_mappings)
    add_pom_ref(meta, EX["mdCodigo"], "Codigo", g_mappings)
    add_pom_ref(meta, EX["mdNota"], "Nota", g_mappings)

    if parameters.get("det") == 2:
        add_pom_parenttpm(meta, EX["variable"], INELOD[table_name + "_Variable"], "Variable.Id", "Variable.Id", g_mappings)
    else:
        add_pom_ref(meta, EX["variable"], "Variable.Id", g_mappings)

def _add_variable_triplesmap(table_name, parameters, g_mappings):
    variable = INELOD[table_name + "_Variable"]
    g_mappings.add((variable, RDF.type, RML.TriplesMap))
    g_mappings.add((variable, RML.logicalSource, INELOD["LS_Meta"]))

    add_subject_map(variable, QB["concept"], g_mappings, template="https://stats.linkeddata.es/voc/cubes/" + "variable/{Variable.Id}")

    add_pom_ref(variable, RDFS.label, "Variable.Nombre", g_mappings)
    add_pom_ref(variable, EX["codigo"], "Variable.Codigo", g_mappings)
    add_pom_ref(variable, EX["id"], "Variable.Id", g_mappings, datatype=XSD.integer)