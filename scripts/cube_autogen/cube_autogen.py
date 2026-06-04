import csv
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import os
import time
import argparse
import sys
import shutil
import tempfile
import unicodedata
import re
import rdflib

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))  # scripts/cube_autogen
SCRIPTS_DIR  = os.path.dirname(SCRIPT_DIR)                  # scripts/
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)                 # LinkedOpenDataINE/
OUTPUT_DIR   = PROJECT_ROOT

RDF_VOC_DIR     = os.path.join(PROJECT_ROOT, "rdf-vocabularies")
INELOD_VOC_PATH = os.path.join(RDF_VOC_DIR, "inelod-voc.ttl")

# Directorio donde se prepara la COPIA de trabajo del CSV.
# El CSV de origen NUNCA se modifica.
PREPARED_DIR = os.path.join(OUTPUT_DIR, "_prepared_csv")

print(f"Script ubicado en:  {SCRIPT_DIR}")
print(f"Raíz del proyecto:  {PROJECT_ROOT}")
print(f"Vocabulario:        {INELOD_VOC_PATH}")

if not os.path.exists(INELOD_VOC_PATH):
    print(f"Advertencia: vocabulario no encontrado en {INELOD_VOC_PATH}", file=sys.stderr)
    print(f"Contenido de rdf-vocabularies: "
          f"{os.listdir(RDF_VOC_DIR) if os.path.exists(RDF_VOC_DIR) else 'CARPETA NO ENCONTRADA'}",
          file=sys.stderr)

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
EX          = Namespace("http://example.org/")
DCAT        = Namespace("http://www.w3.org/ns/dcat#")
SCHEMA      = Namespace("http://schema.org/")
RR          = Namespace("http://www.w3.org/ns/r2rml#")
RML         = Namespace("http://semweb.mmlab.be/ns/rml#")
QL          = Namespace("http://semweb.mmlab.be/ns/ql#")
TRANSIT     = Namespace("http://vocab.org/transit/terms/")
XSD         = Namespace("http://www.w3.org/2001/XMLSchema#")
WGS84_POS   = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
INELOD      = Namespace("http://lod.ine.es/recurso/cubes/")
RDF         = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS        = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL         = Namespace("http://www.w3.org/2002/07/owl#")
SKOS        = Namespace("http://www.w3.org/2004/02/skos/core#")
VOID        = Namespace("http://rdfs.org/ns/void#")
DCT         = Namespace("http://purl.org/dc/terms/")
FOAF        = Namespace("http://xmlns.com/foaf/0.1/")
ORG         = Namespace("http://www.w3.org/ns/org#")
ADMINGEO    = Namespace("http://data.ordnancesurvey.co.uk/dimensions/admingeo/")
INTERVAL    = Namespace("http://reference.data.gov.uk/def/intervals/")
QB          = Namespace("http://purl.org/linked-data/cube#")
SDMX_CONCEPT    = Namespace("http://purl.org/linked-data/sdmx/2009/concept#")
SDMX_DIMENSION  = Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
SDMX_ATTRIBUTE  = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
SDMX_MEASURE    = Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
SDMX_METADATA   = Namespace("http://purl.org/linked-data/sdmx/2009/metadata#")
SDMX_CODE       = Namespace("http://purl.org/linked-data/sdmx/2009/code#")
SDMX_SUBJECT    = Namespace("http://purl.org/linked-data/sdmx/2009/subject#")
INELOD_VOC  = Namespace("http://lod.ine.es/def/vocabulary/")

# Prefijo IRI para las consultas SPARQL contra el vocabulario INE.
# IMPORTANTE: debe coincidir EXACTAMENTE con el namespace usado en
# inelod-voc.ttl. La versión "optimizada" usaba ".../vocabulary/#"
# (con '/#'), lo que rompía la detección de MeasureSet.
INE_VOC_IRI = str(INELOD_VOC)

# ---------------------------------------------------------------------------
# Grafo de mappings RML
# ---------------------------------------------------------------------------
g_mappings = Graph()
for prefix, ns in {
    "ex": EX, "schema": SCHEMA, "rr": RR, "rml": RML, "ql": QL,
    "transit": TRANSIT, "xsd": XSD, "wgs84_pos": WGS84_POS,
    "inelod": INELOD, "rdf": RDF, "rdfs": RDFS, "owl": OWL, "skos": SKOS,
    "void": VOID, "dct": DCT, "foaf": FOAF, "org": ORG, "admingeo": ADMINGEO,
    "interval": INTERVAL, "qb": QB, "sdmx-concept": SDMX_CONCEPT,
    "sdmx-dimension": SDMX_DIMENSION, "sdmx-attribute": SDMX_ATTRIBUTE,
    "sdmx-measure": SDMX_MEASURE, "sdmx-metadata": SDMX_METADATA,
    "sdmx-code": SDMX_CODE, "sdmx-subject": SDMX_SUBJECT,
    "inelod-voc": INELOD_VOC,
}.items():
    g_mappings.bind(prefix, ns)


class OntologyPropertyException(Exception):
    """Columna del CSV sin correspondencia en la ontología."""
    pass


# ===========================================================================
# Utilidades
# ===========================================================================

def _is_empty_row(row):
    """Devuelve True si la fila no tiene ninguna celda con contenido."""
    return not any(cell.strip() for cell in row)


def _normalize_col_name(name):
    """
    Convierte un nombre de columna a ASCII puro para que morph-kgc
    pueda leerlo independientemente de la codificación del sistema.

    Ejemplos:
      'Características básicas de la explotación' → 'Caracteristicas_basicas_de_la_explotacion'
      'Comunidades y Ciudades Autónomas'          → 'Comunidades_y_Ciudades_Autonomas'
      'Cultivos, pastos y huertos'                → 'Cultivos_pastos_y_huertos'
    """
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd.encode('ascii', 'ignore').decode('ascii')
    safe = re.sub(r'[^A-Za-z0-9]+', '_', ascii_str)
    return safe.strip('_')


def _sparql_str(value):
    """Escapa un literal para insertarlo de forma segura en una consulta SPARQL."""
    return value.replace('\\', '\\\\').replace('"', '\\"')


def _str_filter_query(prefixes, where_pattern, label_value, select=None):
    """
    Construye una consulta SPARQL usando FILTER(STR(?label) = "...") en lugar de
    coincidencia exacta con etiqueta de idioma. Esto tolera que el vocabulario
    tenga las etiquetas con '@es', sin idioma, o con otra variante.
    """
    head = "SELECT " + select if select else "ASK"
    body = (
        f"{prefixes} {head} {{ {where_pattern} ; rdfs:label ?__lbl . "
        f'FILTER(STR(?__lbl) = "{_sparql_str(label_value)}") }}'
    )
    return body


def _make_working_copy(source_path):
    """
    Crea una COPIA de trabajo del CSV de origen en PREPARED_DIR, dejando el
    fichero original intacto. La copia conserva el MISMO nombre de fichero
    (para que los URIs derivados del basename no cambien) y se reescribe
    siempre en UTF-8, detectando la codificación de origen.

    Los CSV del INE suelen venir en cp1252 / ISO-8859-15, no en UTF-8; por eso
    se intentan varias codificaciones de lectura. Esto resuelve los problemas
    de codificación sin alterar la fuente.

    Devuelve la ruta de la copia de trabajo.
    """
    os.makedirs(PREPARED_DIR, exist_ok=True)
    working_path = os.path.join(PREPARED_DIR, os.path.basename(source_path))

    raw = None
    used_enc = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(source_path, "r", encoding=enc, newline="") as f:
                raw = f.read()
            used_enc = enc
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        # Último recurso: leer reemplazando bytes inválidos
        with open(source_path, "r", encoding="utf-8", errors="replace", newline="") as f:
            raw = f.read()
        used_enc = "utf-8 (con reemplazo de bytes inválidos)"

    with open(working_path, "w", encoding="utf-8", newline="") as f:
        f.write(raw)

    print(f"  Copia de trabajo creada: {working_path}")
    print(f"  Codificación de origen detectada: {used_enc}")
    print(f"  (El CSV de origen NO se modifica)")
    return working_path


# ===========================================================================
# Funciones de procesamiento del CSV (operan SIEMPRE sobre la copia de trabajo)
# ===========================================================================

def csv_add_index(file_path):
    """
    Añade la columna 'index' como primera columna del CSV de trabajo.
    No normaliza el resto de cabeceras aquí; eso lo hace
    _normalize_csv_headers() después de generar el mapping.
    """
    with open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader, None)
        if headers is None:
            raise ValueError("El CSV está vacío o no tiene cabecera.")
        headers = [h.lstrip('\ufeff') for h in headers]
        if "index" in headers:
            print("  Columna 'index' ya existe, se omite")
            return
        rows = [row for row in reader if not _is_empty_row(row)]

    headers.insert(0, "index")
    indexed_rows = [[str(i)] + row for i, row in enumerate(rows, start=1)]

    with open(file_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        writer.writerows(indexed_rows)

    print(f"  Columna 'index' añadida ({len(indexed_rows)} filas)")


def _normalize_csv_headers(file_path):
    """
    Reescribe las cabeceras del CSV de trabajo a sus versiones ASCII
    normalizadas, para que coincidan con los rml:reference del mapping ya
    generado. Debe llamarse DESPUÉS de serializar el mapping y ANTES de morph-kgc.
    """
    with open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader, None)
        if headers is None:
            return
        rows = [row for row in reader if not _is_empty_row(row)]

    # index ya está normalizado; normalizar el resto
    normalized = [_normalize_col_name(h) if h != 'index' else h
                  for h in headers]

    if normalized == headers:
        print("  Cabeceras ya en ASCII, no es necesario normalizar")
        return

    print(f"  Normalizando cabeceras CSV a ASCII:")
    for orig, norm in zip(headers, normalized):
        if orig != norm:
            print(f"    '{orig}' → '{norm}'")

    fd, tmp = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        with open(tmp, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(normalized)
            writer.writerows(rows)
        shutil.move(tmp, file_path)
    except Exception:
        try: os.remove(tmp)
        except Exception: pass
        raise


def detect_and_replace_measures(file_path, measure, vocabulary):
    """
    Detecta dinámicamente columnas que corresponden a conjuntos de medidas (ine:MeasureSet)
    y reemplaza las etiquetas por sus URIs.

    Proceso:
    1. Consulta el vocabulario para obtener todos los ine:MeasureSet y sus rdfs:label
    2. Identifica columnas del CSV cuyas etiquetas coinciden con las de algún MeasureSet
    3. Para cada valor en esas columnas, busca la ine:MeasureProperty correspondiente
       dentro de ese MeasureSet y reemplaza el valor por su URI
    4. También renombra 'Total' → measure si se especifica

    Si no hay nada que hacer, retorna sin tocar el archivo.
    """
    # -- Leer cabecera --
    with open(file_path, mode='r', encoding='utf-8', errors='replace', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader, None)
    if headers is None:
        return

    # -- Detectar MeasureSets en el vocabulario y sus columnas correspondientes --
    # Query: obtener todos los MeasureSet con su label
    q_measure_sets = (
        f'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> '
        f'PREFIX ine:  <{INE_VOC_IRI}> '
        f'SELECT ?set ?label WHERE {{ ?set a ine:MeasureSet ; rdfs:label ?label . }}'
    )
    
    measure_set_mappings = {}  # {columna_index: (ine:MeasureSet_uri, set_label)}
    for row in vocabulary.query(q_measure_sets):
        set_uri = row["set"]
        set_label = str(row["label"])  # e.g., "Tipo de importe", "Medida"
        # Buscar si alguna columna del CSV tiene este label
        try:
            col_idx = headers.index(set_label)
            measure_set_mappings[col_idx] = (set_uri, set_label)
            print(f"  Detectado MeasureSet '{set_label}' en columna {col_idx}")
        except ValueError:
            # Esta columna no está en el CSV
            pass

    # -- Condición 1: ya está renombrado, nada que hacer --
    if measure and any(h == measure for h in headers):
        return

    # -- Preparar renombre de Total → measure --
    renamed = False
    if measure and "Total" in headers:
        headers = [measure if h == "Total" else h for h in headers]
        renamed = True
        print(f"  Renombrando columna 'Total' → '{measure}'")

    # -- Condición 2: nada que hacer (ni renombrar ni reemplazar URIs) --
    if not renamed and not measure_set_mappings:
        return

    # -- Reescribir el archivo de trabajo --
    fd, tmp = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        with open(file_path, mode='r', encoding='utf-8', errors='replace', newline='') as src, \
             open(tmp,       mode='w', encoding='utf-8', newline='') as dst:
            reader = csv.reader(src, delimiter=';')
            writer = csv.writer(dst, delimiter=';')

            next(reader, None)          # descartar cabecera original
            writer.writerow(headers)    # escribir cabecera actualizada

            for row in reader:
                if _is_empty_row(row):  # descartar filas vacías
                    continue
                
                # Reemplazar etiquetas por URIs en columnas de MeasureSet
                for col_idx, (set_uri, set_label) in measure_set_mappings.items():
                    if col_idx < len(row):
                        cell_value = row[col_idx]
                        if cell_value:
                            # Buscar la ine:MeasureProperty dentro de este MeasureSet
                            # cuyo rdfs:label coincida con el valor de la celda
                            q = (
                                f'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> '
                                f'PREFIX ine:  <{INE_VOC_IRI}> '
                                f'SELECT ?measure WHERE {{ '
                                f'  ?measure ine:inMeasureSet <{set_uri}> ; '
                                f'           rdfs:label ?label . '
                                f'  FILTER(STR(?label) = "{_sparql_str(cell_value)}") '
                                f'}}'
                            )
                            for res in vocabulary.query(q):
                                row[col_idx] = str(res["measure"])
                                break
                
                writer.writerow(row)

        shutil.move(tmp, file_path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


# ===========================================================================
# Funciones de generación de mappings RML
# ===========================================================================

def add_INE_metadata(file_path, measure):
    """Genera los TriplesMap DCAT (Dataset + Distribuciones) en g_mappings."""
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    dataset_uri         = INELOD[file_name]
    triples_map_dataset = INELOD[file_name + "_TriplesMapDataset"]

    g_mappings.add((triples_map_dataset, RDF.type, RR.TriplesMap))

    ls = BNode()
    g_mappings.add((triples_map_dataset, RML.logicalSource, ls))
    g_mappings.add((ls, RML.source,               Literal(file_path)))
    g_mappings.add((ls, RML.referenceFormulation, QL.CSV))

    sm = BNode()
    g_mappings.add((triples_map_dataset, RR.subjectMap, sm))
    g_mappings.add((sm, RR.constant,   dataset_uri))
    g_mappings.add((sm, RR["class"],   QB.DataSet))

    def add_pom(pred, obj, lang=None):
        pom = BNode()
        g_mappings.add((triples_map_dataset, RR.predicateObjectMap, pom))
        g_mappings.add((pom, RR.predicate, pred))
        if lang:
            g_mappings.add((pom, RR.object, Literal(obj, lang=lang)))
        else:
            g_mappings.add((pom, RR.object, obj if isinstance(obj, URIRef) else Literal(obj)))

    add_pom(RDFS.label,       file_name)
    add_pom(DCT.license,      URIRef("https://creativecommons.org/licenses/by/4.0/"))
    add_pom(DCT.source,       URIRef(f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}"))
    add_pom(RDF.type,         DCAT.Dataset)
    add_pom(DCT.identifier,   Literal(f"urn:ine:es:TABLA:TPX:{file_name}", lang="es"))
    add_pom(DCT.language,     URIRef("http://publications.europa.eu/resource/authority/language/SPA"))
    add_pom(DCAT.contactPoint,URIRef("https://www.ine.es/"))
    add_pom(DCT.publisher,    URIRef("https://www.ine.es/"))
    add_pom(QB.structure,     INELOD[file_name + "_dsd"])

    # Distribuciones
    distributions = [
        {"suffix": "dist_html",  "title": [("Html","es"),("Html","en")],
         "format": "http://publications.europa.eu/resource/authority/file-type/HTML",
         "mediaType": "http://www.iana.org/assignments/media-types/text/html",
         "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}"},
        {"suffix": "dist_px",    "title": [("PC-Axis","es"),("PC-Axis","en")],
         "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
         "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/px/{file_name}.px?nocab=1"},
        {"suffix": "dist_xlsx",  "title": [("Excel: Extensión XLSX","es"),("Excel: XLSX extension","en")],
         "format": "http://publications.europa.eu/resource/authority/file-type/XLSX",
         "mediaType": "http://www.iana.org/assignments/media-types/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
         "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/xlsx/{file_name}.xlsx?nocab=1"},
        {"suffix": "dist_json",  "title": [("Json","es"),("Json","en")],
         "format": "http://publications.europa.eu/resource/authority/file-type/JSON",
         "mediaType": "http://www.iana.org/assignments/media-types/application/json",
         "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
         "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/json/t{file_name}.json?nocab=1"},
        {"suffix": "dist_csv_tab","title": [("CSV: separado por tabuladores","es"),("CSV: Tab Separated","en")],
         "format": "http://publications.europa.eu/resource/authority/file-type/CSV",
         "mediaType": "http://www.iana.org/assignments/media-types/text/csv",
         "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
         "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/csv_bd/{file_name}.csv?nocab=1"},
        {"suffix": "dist_csv_sc", "title": [("CSV: separado por ;","es"),("CSV: Separated by ;","en")],
         "format": "http://publications.europa.eu/resource/authority/file-type/CSV",
         "mediaType": "http://www.iana.org/assignments/media-types/text/csv",
         "accessURL": f"https://www.ine.es/jaxiT3/Tabla.htm?t={file_name}",
         "downloadURL": f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{file_name}.csv?nocab=1"},
    ]

    for d in distributions:
        dist_uri = INELOD[file_name + "_" + d["suffix"]]
        tm       = INELOD[file_name + "_TM_" + d["suffix"]]

        g_mappings.add((tm, RDF.type, RR.TriplesMap))
        ls2 = BNode()
        g_mappings.add((tm, RML.logicalSource, ls2))
        g_mappings.add((ls2, RML.source,               Literal(file_path)))
        g_mappings.add((ls2, RML.referenceFormulation, QL.CSV))
        sm2 = BNode()
        g_mappings.add((tm, RR.subjectMap, sm2))
        g_mappings.add((sm2, RR.constant, dist_uri))

        # Enlazar dataset → distribución
        pom_link = BNode(); obj_map = BNode()
        g_mappings.add((triples_map_dataset, RR.predicateObjectMap, pom_link))
        g_mappings.add((pom_link, RR.predicate,  DCAT.distribution))
        g_mappings.add((pom_link, RR.objectMap,  obj_map))
        g_mappings.add((obj_map,  RR.parentTriplesMap, tm))

        def _add_dist_pom(pred, obj):
            p = BNode()
            g_mappings.add((tm, RR.predicateObjectMap, p))
            g_mappings.add((p, RR.predicate, pred))
            g_mappings.add((p, RR.object,    obj))

        _add_dist_pom(RDF.type,                DCAT.Distribution)
        _add_dist_pom(DCT.license,             URIRef("https://www.ine.es/aviso_legal"))
        _add_dist_pom(DCAT.applicableLegislation, URIRef("http://data.europa.eu/eli/reg_impl/2023/138/oj"))
        _add_dist_pom(DCAT.accessURL,          URIRef(d["accessURL"]))
        if "downloadURL" in d:
            _add_dist_pom(DCAT.downloadURL,    URIRef(d["downloadURL"]))
        if "format" in d:
            _add_dist_pom(DCT["format"],       URIRef(d["format"]))
        if "mediaType" in d:
            _add_dist_pom(DCAT.mediaType,      URIRef(d["mediaType"]))
        for title, lang in d["title"]:
            p = BNode()
            g_mappings.add((tm, RR.predicateObjectMap, p))
            g_mappings.add((p, RR.predicate, DCT.title))
            g_mappings.add((p, RR.object,    Literal(title, lang=lang)))


def add_POM_from_csv(file_path, measure):
    """
    Genera los TriplesMap del DSD (componentes) y los predicateObjectMap
    de las observaciones a partir de las columnas del CSV de trabajo.
    """
    print(f"  Cargando vocabulario desde: {INELOD_VOC_PATH}")
    try:
        with open(INELOD_VOC_PATH, 'r', encoding='utf-8') as vf:
            vocabulary = Graph().parse(vf, format='turtle')
    except FileNotFoundError:
        raise OntologyPropertyException(
            f"Vocabulario no encontrado: {INELOD_VOC_PATH}")
    except Exception as e:
        raise OntologyPropertyException(f"Error cargando vocabulario: {e}")

    file_name = os.path.splitext(os.path.basename(file_path))[0]
    dsd_uri   = INELOD[file_name + "_dsd"]
    tm_dsd    = INELOD[file_name + "_TriplesMapDSD"]
    tm_obs    = INELOD[file_name + "_Observations"]

    # TriplesMap del DSD
    g_mappings.add((tm_dsd, RDF.type, RR.TriplesMap))
    ls = BNode()
    g_mappings.add((tm_dsd, RML.logicalSource, ls))
    g_mappings.add((ls, RML.source,               Literal(file_path)))
    g_mappings.add((ls, RML.referenceFormulation, QL.CSV))
    sm = BNode()
    g_mappings.add((tm_dsd, RR.subjectMap, sm))
    g_mappings.add((sm, RR.constant,   dsd_uri))
    g_mappings.add((sm, RR["class"],   QB.DataStructureDefinition))

    detect_and_replace_measures(file_path, measure, vocabulary)

    with open(file_path, mode='r', encoding='utf-8') as f:
        columns = csv.DictReader(f, delimiter=';').fieldnames

    # Prefijos SPARQL reutilizables
    PFX_DIM = ('PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>'
               'PREFIX qb: <http://purl.org/linked-data/cube#>')
    PFX_SET = ('PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>'
               f'PREFIX ine: <{INE_VOC_IRI}>')

    order = 1
    for column in columns:
        if column == "index":
            continue

        # Clasificación tolerante (FILTER STR en lugar de coincidencia "@es")
        is_dim = vocabulary.query(_str_filter_query(
            PFX_DIM, '?s a qb:DimensionProperty', column)).askAnswer
        is_mea = vocabulary.query(_str_filter_query(
            PFX_DIM, '?s a qb:MeasureProperty', column)).askAnswer
        is_set = vocabulary.query(_str_filter_query(
            PFX_SET, '?s a ine:MeasureSet', column)).askAnswer

        print(f"  Columna '{column}': dim={is_dim} mea={is_mea} set={is_set}")

        # ── DIMENSIÓN ────────────────────────────────────────────────────────
        if is_dim and not is_mea and not is_set:
            dim_uri = next(
                (URIRef(r["s"]) for r in vocabulary.query(_str_filter_query(
                    PFX_DIM, '?s a qb:DimensionProperty', column, select='?s'))),
                None)
            if dim_uri is None:
                raise OntologyPropertyException(f"Sin URI para dimensión '{column}'")

            comp_uri = INELOD[f"{file_name}_component_{order}"]
            # Componente del DSD
            tm_comp = INELOD[f"{file_name}_TM_component_{order}"]
            g_mappings.add((tm_comp, RDF.type, RR.TriplesMap))
            ls2 = BNode()
            g_mappings.add((tm_comp, RML.logicalSource, ls2))
            g_mappings.add((ls2, RML.source,               Literal(file_path)))
            g_mappings.add((ls2, RML.referenceFormulation, QL.CSV))
            sm2 = BNode()
            g_mappings.add((tm_comp, RR.subjectMap, sm2))
            g_mappings.add((sm2, RR.constant, comp_uri))
            for pred, obj in [(QB.dimension, dim_uri),
                              (QB.order,     Literal(order, datatype=XSD.integer))]:
                p = BNode()
                g_mappings.add((tm_comp, RR.predicateObjectMap, p))
                g_mappings.add((p, RR.predicate, pred))
                g_mappings.add((p, RR.object,    obj))
            # Enlace DSD → componente
            pom_comp = BNode(); obj_map = BNode()
            g_mappings.add((tm_dsd, RR.predicateObjectMap, pom_comp))
            g_mappings.add((pom_comp, RR.predicate,  QB.component))
            g_mappings.add((pom_comp, RR.objectMap,  obj_map))
            g_mappings.add((obj_map,  RR.parentTriplesMap, tm_comp))
            # Predicado en observación — reference normalizado para morph-kgc
            pom_obs = BNode(); obj_ref = BNode()
            g_mappings.add((tm_obs, RR.predicateObjectMap, pom_obs))
            g_mappings.add((pom_obs, RR.predicate,  dim_uri))
            g_mappings.add((pom_obs, RR.objectMap,  obj_ref))
            g_mappings.add((obj_ref, RML.reference, Literal(_normalize_col_name(column))))
            order += 1
            continue

        # ── MEDIDA INDIVIDUAL ────────────────────────────────────────────────
        if not is_dim and is_mea and not is_set:
            mea_uri = next(
                (URIRef(r["s"]) for r in vocabulary.query(_str_filter_query(
                    PFX_DIM, '?s a qb:MeasureProperty', column, select='?s'))),
                None)
            if mea_uri is None:
                raise OntologyPropertyException(f"Sin URI para medida '{column}'")

            comp_uri = INELOD[f"{file_name}_component_measu"]
            tm_comp  = INELOD[f"{file_name}_TM_component_measu"]
            g_mappings.add((tm_comp, RDF.type, RR.TriplesMap))
            ls2 = BNode()
            g_mappings.add((tm_comp, RML.logicalSource, ls2))
            g_mappings.add((ls2, RML.source,               Literal(file_path)))
            g_mappings.add((ls2, RML.referenceFormulation, QL.CSV))
            sm2 = BNode()
            g_mappings.add((tm_comp, RR.subjectMap, sm2))
            g_mappings.add((sm2, RR.constant, comp_uri))
            p = BNode()
            g_mappings.add((tm_comp, RR.predicateObjectMap, p))
            g_mappings.add((p, RR.predicate, QB.measure))
            g_mappings.add((p, RR.object,    mea_uri))
            pom_comp = BNode(); obj_map = BNode()
            g_mappings.add((tm_dsd, RR.predicateObjectMap, pom_comp))
            g_mappings.add((pom_comp, RR.predicate,  QB.component))
            g_mappings.add((pom_comp, RR.objectMap,  obj_map))
            g_mappings.add((obj_map,  RR.parentTriplesMap, tm_comp))
            pom_obs = BNode(); obj_ref = BNode()
            g_mappings.add((tm_obs, RR.predicateObjectMap, pom_obs))
            g_mappings.add((pom_obs, RR.predicate,  mea_uri))
            g_mappings.add((pom_obs, RR.objectMap,  obj_ref))
            g_mappings.add((obj_ref, RML.reference, Literal(_normalize_col_name(column))))
            g_mappings.add((obj_ref, RR.datatype,   XSD.float))
            continue

        # ── GRUPO DE MEDIDAS (measureType) ───────────────────────────────────
        if not is_dim and not is_mea and is_set:
            comp_uri = INELOD[f"{file_name}_component_{order}"]
            tm_comp  = INELOD[f"{file_name}_TM_component_{order}"]
            g_mappings.add((tm_comp, RDF.type, RR.TriplesMap))
            ls2 = BNode()
            g_mappings.add((tm_comp, RML.logicalSource, ls2))
            g_mappings.add((ls2, RML.source,               Literal(file_path)))
            g_mappings.add((ls2, RML.referenceFormulation, QL.CSV))
            sm2 = BNode()
            g_mappings.add((tm_comp, RR.subjectMap, sm2))
            g_mappings.add((sm2, RR.constant, comp_uri))
            for pred, obj in [(QB.dimension, QB.measureType),
                              (QB.order,     Literal(order, datatype=XSD.integer))]:
                p = BNode()
                g_mappings.add((tm_comp, RR.predicateObjectMap, p))
                g_mappings.add((p, RR.predicate, pred))
                g_mappings.add((p, RR.object,    obj))
            pom_comp = BNode(); obj_map = BNode()
            g_mappings.add((tm_dsd, RR.predicateObjectMap, pom_comp))
            g_mappings.add((pom_comp, RR.predicate,  QB.component))
            g_mappings.add((pom_comp, RR.objectMap,  obj_map))
            g_mappings.add((obj_map,  RR.parentTriplesMap, tm_comp))
            pom_obs = BNode(); obj_ref = BNode()
            g_mappings.add((tm_obs, RR.predicateObjectMap, pom_obs))
            g_mappings.add((pom_obs, RR.predicate,  QB.measureType))
            g_mappings.add((pom_obs, RR.objectMap,  obj_ref))
            g_mappings.add((obj_ref, RML.reference, Literal(_normalize_col_name(column))))
            g_mappings.add((obj_ref, RR.termType,   RR.IRI))
            val_pom = BNode(); pred_map = BNode(); val_obj = BNode()
            g_mappings.add((tm_obs, RR.predicateObjectMap, val_pom))
            g_mappings.add((val_pom, RR.predicateMap, pred_map))
            g_mappings.add((pred_map, RML.reference, Literal(_normalize_col_name(column))))
            g_mappings.add((pred_map, RR.termType,   RR.IRI))
            g_mappings.add((val_pom, RR.objectMap,   val_obj))
            g_mappings.add((val_obj, RML.reference,  Literal(_normalize_col_name(measure) if measure else "Total")))
            g_mappings.add((val_obj, RR.datatype,    XSD.float))
            order += 1
            # Medidas del grupo
            sel_set = _str_filter_query(
                PFX_SET,
                '?ms a ine:MeasureSet',
                column,
                select='?m',
            )
            # añadir el patrón de pertenencia ?m ine:inMeasureSet ?ms
            sel_set = sel_set.replace(
                '?ms a ine:MeasureSet ; rdfs:label ?__lbl .',
                '?ms a ine:MeasureSet ; rdfs:label ?__lbl . ?m ine:inMeasureSet ?ms .'
            )
            for i, r in enumerate(vocabulary.query(sel_set), start=1):
                mea_uri  = URIRef(r["m"])
                comp_m   = INELOD[f"{file_name}_component_measu{i}"]
                tm_comp_m = INELOD[f"{file_name}_TM_component_measu{i}"]
                g_mappings.add((tm_comp_m, RDF.type, RR.TriplesMap))
                ls3 = BNode()
                g_mappings.add((tm_comp_m, RML.logicalSource, ls3))
                g_mappings.add((ls3, RML.source,               Literal(file_path)))
                g_mappings.add((ls3, RML.referenceFormulation, QL.CSV))
                sm3 = BNode()
                g_mappings.add((tm_comp_m, RR.subjectMap, sm3))
                g_mappings.add((sm3, RR.constant, comp_m))
                p = BNode()
                g_mappings.add((tm_comp_m, RR.predicateObjectMap, p))
                g_mappings.add((p, RR.predicate, QB.measure))
                g_mappings.add((p, RR.object,    mea_uri))
                pom_link = BNode(); obj_map2 = BNode()
                g_mappings.add((tm_dsd, RR.predicateObjectMap, pom_link))
                g_mappings.add((pom_link, RR.predicate,  QB.component))
                g_mappings.add((pom_link, RR.objectMap,  obj_map2))
                g_mappings.add((obj_map2, RR.parentTriplesMap, tm_comp_m))
            continue

        # ── COLUMNA DE VALORES (Total) cuando hay MeasureSet ──────────────────
        # Si la columna no se clasificó pero es la columna de valores (Total o renombrada),
        # simplemente saltarla: ya fue procesada en la rama del MeasureSet.
        value_col_name = measure if measure else "Total"
        if column == value_col_name and not is_dim and not is_mea and not is_set:
            # Es la columna de valores; ya está manejada en un MeasureSet procesado antes
            continue

        raise OntologyPropertyException(
            f"La columna '{column}' no está definida en la ontología "
            f"(dim={is_dim}, mea={is_mea}, set={is_set})."
        )


def add_mappings_from_csv(file_path):
    """Genera el TriplesMap de observaciones (cabecera + subjectMap)."""
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    tm_obs    = INELOD[file_name + "_Observations"]

    g_mappings.add((tm_obs, RDF.type, RR.TriplesMap))
    ls = BNode()
    g_mappings.add((tm_obs, RML.logicalSource, ls))
    g_mappings.add((ls, RML.source,               Literal(file_path)))
    g_mappings.add((ls, RML.referenceFormulation, QL.CSV))
    sm = BNode()
    g_mappings.add((tm_obs, RR.subjectMap, sm))
    g_mappings.add((sm, RR.template, Literal(
        f"http://lod.ine.es/recurso/cubes/{file_name}/o{{index}}")))
    g_mappings.add((sm, RR["class"],  QB.Observation))
    pom = BNode()
    g_mappings.add((tm_obs, RR.predicateObjectMap, pom))
    g_mappings.add((pom, RR.predicate, QB.dataSet))
    g_mappings.add((pom, RR.object,    INELOD[file_name]))


# ===========================================================================
# Pipeline principal
# ===========================================================================

def run(csv_file_path, measure):
    basename     = os.path.splitext(os.path.basename(csv_file_path))[0]
    mapping_file = os.path.join(OUTPUT_DIR, "auto_mappings.ttl")
    output_file  = os.path.join(OUTPUT_DIR, f"{basename}.nt")
    mappings_dst = os.path.join(OUTPUT_DIR, f"auto_mappings_{basename}.ttl")

    # ── 0) Copia de trabajo: el CSV de origen NO se modifica ────────────────
    t = time.time()
    work_path = _make_working_copy(csv_file_path)
    print(f"[0/6] Copia de trabajo preparada en {time.time()-t:.2f}s")

    # A partir de aquí, TODO opera sobre la copia (work_path).
    t = time.time()
    add_INE_metadata(work_path, measure)
    print(f"[1/6] Metadatos DCAT generados en {time.time()-t:.2f}s")

    t = time.time()
    csv_add_index(work_path)
    print(f"[2/6] Index añadido a la copia en {time.time()-t:.2f}s")

    t = time.time()
    add_POM_from_csv(work_path, measure)   # incluye detect_and_replace_measures
    print(f"[3/6] DSD y predicados de observaciones generados en {time.time()-t:.2f}s")

    t = time.time()
    add_mappings_from_csv(work_path)
    print(f"[4/6] TriplesMap de observaciones generado en {time.time()-t:.2f}s")

    t = time.time()
    g_mappings.serialize(format='turtle', destination=mapping_file)
    print(f"[5/6] Mappings serializados en {mapping_file} ({time.time()-t:.2f}s)")

    # Normalizar cabeceras de la copia a ASCII para que coincidan con rml:reference
    t = time.time()
    _normalize_csv_headers(work_path)
    print(f"[6/6] Cabeceras de la copia normalizadas en {time.time()-t:.2f}s")

    # ── Ejecutar morph-kgc ──────────────────────────────────────────────────
    # IMPORTANTE: materialize_set() devuelve un set de N-Triples en memoria y
    # NO escribe output_file_path. Hay que capturar el resultado y volcarlo a
    # disco nosotros mismos (este era el motivo de que "no se generaran" tripletas).
    t = time.time()
    morph_config = (
        "[CONFIGURATION]\n"
        "\n"
        "[DataSource1]\n"
        f"mappings={mapping_file}\n"
    )
    try:
        import morph_kgc
        print("Ejecutando morph-kgc...")
        print(f"  Mappings: {mapping_file}")
        print(f"  CSV:      {work_path}")
        print(f"  Salida:   {output_file}")
        triples = morph_kgc.materialize_set(morph_config)
    except Exception as e:
        print(f"morph-kgc falló: {e}")
        raise

    # Volcar las tripletas a disco en formato N-Triples
    with open(output_file, "w", encoding="utf-8") as f:
        if triples:
            f.write(".\n".join(sorted(triples)) + ".\n")
    print(f"morph-kgc completado en {time.time()-t:.2f}s")
    print(f"  {len(triples)} tripletas escritas")

    if os.path.exists(mapping_file):
        os.rename(mapping_file, mappings_dst)
        print(f"Mapping guardado en: {mappings_dst}")

    if not triples:
        print("\nADVERTENCIA: se generaron 0 tripletas. Revisa que los "
              "rml:reference del mapping coincidan con las cabeceras de la copia "
              f"({work_path}) y que las columnas estén en el vocabulario.")

    print(f"\nGrafo de conocimiento generado: {output_file}")
    print(f"(CSV de origen intacto: {csv_file_path})")


# ===========================================================================
# CLI
# ===========================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera un cubo RDF (QB + DCAT) a partir de un CSV del INE"
    )
    parser.add_argument("input_csv", help="Ruta al archivo CSV de entrada")
    parser.add_argument("--medida", default=None,
                        help="Nombre de la medida principal (opcional)")
    args = parser.parse_args()

    csv_path = os.path.abspath(args.input_csv)
    if not os.path.exists(csv_path):
        print(f"Error: no se encontró {csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        run(csv_path, args.medida)
        print("\nProceso completado correctamente.")
        sys.exit(0)
    except OntologyPropertyException as e:
        print(f"\nError de ontología: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}", file=sys.stderr)
        sys.exit(1)
