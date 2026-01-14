@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix qb:    <http://purl.org/linked-data/cube#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix dct:   <http://purl.org/dc/terms/> .
@prefix :      <http://example.org/shapes/inelod-qb/> .

#################################################################
# 1. DIMENSION PROPERTIES (qb:DimensionProperty)
#################################################################

:DimensionPropertyShape
    a sh:NodeShape ;
    sh:targetClass qb:DimensionProperty ;

    #################################################################
    # 1.1 Tipo y metadatos básicos.
    #################################################################

    # Tipo explícito
    sh:property [
        sh:path rdf:type ;
        sh:hasValue qb:DimensionProperty ;
        sh:severity sh:Violation ;
        sh:message "Una dimension en el  vocabulario DEBE tener el tipo qb:DimensionProperty." ;
    ] ;

    # Etiqueta legible por humanos.
    sh:property [
        sh:path rdfs:label ;
        sh:datatype rdf:langString ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
        sh:message "A qb:DimensionProperty DEBE tener por lo menos una rdfs:label (con etiqueta de idioma)." ;
    ] ;

    # Descripcion / definicion (recomendado)
    sh:property [
        sh:path rdfs:comment ;
        sh:datatype rdf:langString ;
        sh:minCount 1 ;
        sh:severity sh:Warning ;
        sh:message "Una qb:DimensionProperty DEBERÍA tener un rdfs:comment que describa su significado." ;
    ] ;

    #################################################################
    # 1.2 Rango y codificación
    #################################################################

    # Cada dimension debería declarar un range (la clase de los valores que toma)
    sh:property [
        sh:path rdfs:range ;
        sh:minCount 1 ;
        sh:nodeKind sh:IRI ;
        sh:severity sh:Violation ;
        sh:message "Una qb:DimensionProperty DEBE declarar un rdfs:range (la clase de los valores que toma)." ;
    ] ;

    # Si la dimensión está codificada (usa qb:codeList),
    # la lista de códigos DEBERÍA ser un skos:ConceptScheme
    sh:property [
        sh:path qb:codeList ;
        sh:class skos:ConceptScheme ;
        sh:severity sh:Warning ;
        sh:message "Si un qb:DimensionProperty usa qb:codeList, el objetivo DEBERÍA ser un skos:ConceptScheme." ;
    ] ;

    #################################################################
    # 1.3 Dominio
    #################################################################

    # Cada dimension debería declarar un dominio (la clase de los valores que toma)
    sh:property [
        sh:path rdfs:domain ;
        sh:hasValue qb:Observation ;
        sh:severity sh:Warning ;
        sh:message "Esta RECOMENDADO que qb:DimensionProperty tenga una qb:Observation como dominio." ;
    ] ;

    #################################################################
    # 1.4 Regla de integridad: no DEBE ser también una medida.
    #################################################################

    sh:sparql [
        sh:message "Una propiedad NO DEBE ser ambas qb:DimensionProperty y qb:MeasureProperty." ;
        sh:severity sh:Violation ;
        sh:select """
            SELECT $this
            WHERE {
              $this a qb:MeasureProperty .
            }
        """ ;
    ] .

#################################################################
# 2. MEASURE PROPERTIES (qb:MeasureProperty)
#################################################################

:MeasurePropertyShape
    a sh:NodeShape ;
    sh:targetClass qb:MeasureProperty ;

    #################################################################
    # 2.1 Tipo y metadatos básicos
    #################################################################

    sh:property [
        sh:path rdf:type ;
        sh:hasValue qb:MeasureProperty ;
        sh:severity sh:Violation ;
        sh:message "Una medida del vocabulario DEBE tener el tipo qb:MeasureProperty." ;
    ] ;

    sh:property [
        sh:path rdfs:label ;
        sh:datatype rdf:langString ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
        sh:message "Una qb:MeasureProperty DEBE tener por lo menos un rdfs:label (con etiqueta de idioma)." ;
    ] ;

    sh:property [
        sh:path rdfs:comment ;
        sh:datatype rdf:langString ;
        sh:minCount 1 ;
        sh:severity sh:Warning ;
        sh:message "Una qb:MeasureProperty DEBERÍA tener un rdfs:comment que describa la medida." ;
    ] ;

    #################################################################
    # 2.2 Rango: DEBE ser numerico o por lo menos un datatype
    #################################################################

    # Requiere un datatype range y restringirlo a tipos numéricos comunes.
    sh:property [
        sh:path rdfs:range ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:severity sh:Violation ;
        sh:message "Una qb:MeasureProperty DEBE declarar un (único) rdfs:range tipo de dato para sus valores numéricos" ;
        sh:or (
            [ sh:hasValue xsd:decimal ]
            [ sh:hasValue xsd:double ]
            [ sh:hasValue xsd:float ]
            [ sh:hasValue xsd:integer ]
            [ sh:hasValue xsd:nonNegativeInteger ]
            [ sh:hasValue xsd:positiveInteger ]
        )
    ] ;

    # Opcional: unidad / concepto para la medida
    sh:property [
        sh:path qb:concept ;
        sh:maxCount 1 ;
        sh:severity sh:Info ;
        sh:message "Si se usa, qb:concept DEBERÍA apuntar a un concepto que describa esta medida en un esquema apropiado." ;
    ] ;

    #################################################################
    # 2.3 Dominio
    #################################################################

    sh:property [
        sh:path rdfs:domain ;
        sh:hasValue qb:Observation ;
        sh:severity sh:Warning ;
        sh:message "Se RECOMIENDA que qb:MeasureProperty tenga qb:Observation como dominio." ;
    ] ;

    #################################################################
    # 2.4 Regla de integridad: no DEBE ser una dimension
    #################################################################

    sh:sparql [
        sh:message "Una propiedad NO DEBE ser qb:MeasureProperty y qb:DimensionProperty." ;
        sh:severity sh:Violation ;
        sh:select """
            SELECT $this
            WHERE {
              $this a qb:DimensionProperty .
            }
        """ ;
    ] .

#################################################################
# 3. Propiedades de Atributo
#################################################################

:AttributePropertyShape
    a sh:NodeShape ;
    sh:targetClass qb:AttributeProperty ;

    sh:property [
        sh:path rdf:type ;
        sh:hasValue qb:AttributeProperty ;
        sh:severity sh:Violation ;
        sh:message "Un atributo en el vocabulario DEBE tener el tipo qb:AttributeProperty." ;
    ] ;

    sh:property [
        sh:path rdfs:label ;
        sh:datatype rdf:langString ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
        sh:message "Un qb:AttributeProperty DEBE tener por lo menos un rdfs:label (con etiqueta de idioma)." ;
    ] ;

    sh:property [
        sh:path rdfs:comment ;
        sh:datatype rdf:langString ;
        sh:minCount 1 ;
        sh:severity sh:Warning ;
        sh:message "Un qb:AttributeProperty DEBERÍA tener un rdfs:comment que describa el atributo." ;
    ] ;


    sh:property [
        sh:path rdfs:range ;
        sh:minCount 1 ;
        sh:severity sh:Warning ;
        sh:message "Un qb:AttributeProperty DEBERÍA tener un rdfs:range (tipo de dato o clase)." ;
    ] ;

    sh:property [
        sh:path rdfs:domain ;
        sh:hasValue qb:Observation ;
        sh:severity sh:Warning ;
        sh:message "Se RECOMIENDA que qb:AttributeProperty tenga qb:Observation como dominio." ;
    ] .

#################################################################
# 4. Reglas para asegurar que una propiedad no es más que un tipo.
#################################################################

# 4.1 Una propiedad no es más que un tipo: Dimension, Measure, Attribute

:ComponentPropertyDisjointnessShape
    a sh:NodeShape ;
    sh:target [
        a sh:SPARQLTarget ;
        sh:select """
            SELECT ?this
            WHERE {
              ?this a ?t1, ?t2 .
              FILTER (?t1 IN (qb:DimensionProperty, qb:MeasureProperty, qb:AttributeProperty)) .
              FILTER (?t2 IN (qb:DimensionProperty, qb:MeasureProperty, qb:AttributeProperty)) .
              FILTER (?t1 != ?t2)
            }
        """ ;
    ] ;

    sh:message "Una sola propiedad NO DEBE tener de tipo de dato más de uno de los siguientes: qb:DimensionProperty, qb:MeasureProperty, or qb:AttributeProperty." ;
    sh:severity sh:Violation .
