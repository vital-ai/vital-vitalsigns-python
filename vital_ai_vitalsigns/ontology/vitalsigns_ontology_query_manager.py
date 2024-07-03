

class VitalSignsOntologyQueryManager:
    pass


# nodes like VitalOntNode are defined in the vital domain which is not
# present here (only core is)
# using those classes for ontology representation is handled in the kg service lib

# use domains graph including all domains and sparql queries against rdflib

# get ontology iris that are loaded

# get classes directly under class, or owl:Thing as default if unspecified
# scoped by iri for input

# given class, get parent class(es)
# scoped by iri for input

# given class, get sub class(es)
# scoped by iri for the input

# get triples defining a class, given class uri
# scoped by iri for input

# get data properties under property or all under topDataProperty by default
# scoped by ontology iri

# get object properties under property or all under topObjectProperty by default
# scoped by ontology iri

# given data property, get range
# given data property, get domain

# given object property, get range
# given object property, get domain

# get triples defining property, given property uri
# scoped by iri for input

# get annotations as triples for a class or property uri

# get triples representing ontology given ontology iri

# get annotations as triples on an ontology iri

# get individual uris of a class given class uri
# scoped by ontology iri

# get triples defining an individual given individual uri
# scoped by ontology uri




