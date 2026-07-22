"""Parity regression tests for the python generator (planning/generator-parity-spec.v3.md).

Compares generator output byte-for-byte against the committed
vital_ai_vitalsigns_core package, which is Groovy-generated baseline code.
"""

import os

import pytest
from owlready2 import get_ontology, onto_path

from vital_ai_vitalsigns_generate.generate.domain_ontology_class_generator import DomainOntologyClassGenerator
from vital_ai_vitalsigns_generate.vitalsigns_domain_list_generator import VitalSignsDomainListGenerator

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VITAL_ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'vital_home_test', 'vital-ontology')
VITAL_CORE_OWL = os.path.join(VITAL_ONTOLOGY_DIR, 'vital-core-0.2.304.owl')

COMMITTED_CORE_MODEL_DIR = os.path.join(PROJECT_DIR, 'vital_ai_vitalsigns_core', 'model')

VITAL_CORE_IRI = "http://vital.ai/ontology/vital-core"


@pytest.fixture(scope="module")
def core_ontology():
    onto_path.append(VITAL_ONTOLOGY_DIR)
    ontology = get_ontology("file://" + VITAL_CORE_OWL).load()
    return ontology


@pytest.fixture(scope="module")
def generator():
    return VitalSignsDomainListGenerator()


def read_committed(relative_path):
    with open(os.path.join(COMMITTED_CORE_MODEL_DIR, relative_path)) as f:
        return f.read()


def test_domain_ontology_parity():
    generated = DomainOntologyClassGenerator.generate(VITAL_CORE_IRI)
    assert generated == read_committed('DomainOntology.py')


@pytest.mark.parametrize("class_name", ["Dataset", "Edge_SameAs", "VITAL_PeerEdge"])
def test_class_py_parity(generator, core_ontology, class_name):
    ont_class = core_ontology.search_one(iri=f"{VITAL_CORE_IRI}#{class_name}")
    assert ont_class is not None
    generated = generator.generate_class_code([core_ontology], core_ontology, ont_class)
    assert generated == read_committed(f'{class_name}.py')


@pytest.mark.parametrize("class_name", ["Dataset", "Edge_SameAs", "VITAL_PeerEdge"])
def test_class_pyi_parity(generator, core_ontology, class_name):
    ont_class = core_ontology.search_one(iri=f"{VITAL_CORE_IRI}#{class_name}")
    assert ont_class is not None
    generated = generator.generate_class_interface_code([core_ontology], core_ontology, ont_class)
    assert generated == read_committed(f'{class_name}.pyi')


@pytest.mark.parametrize("prop_name", ["hasName", "types"])
def test_property_trait_parity(generator, core_ontology, prop_name):
    ont_prop = core_ontology.search_one(iri=f"{VITAL_CORE_IRI}#{prop_name}")
    assert ont_prop is not None
    generated = generator.generate_property_code(core_ontology, ont_prop)
    assert generated == read_committed(f'properties/Property_{prop_name}.py')


def test_trait_file_set_parity(generator, core_ontology):
    """The set of generated trait files must equal the committed set
    (validates annotation-property and non-graph-object filtering)."""
    generated_names = {
        'Property_' + p.name + '.py'
        for p in core_ontology.properties()
        if generator.should_generate_trait(core_ontology, p)
    }
    committed_names = {
        f for f in os.listdir(os.path.join(COMMITTED_CORE_MODEL_DIR, 'properties'))
        if f.startswith('Property_') and f.endswith('.py')
    }
    assert generated_names == committed_names


def test_class_file_set_parity(generator, core_ontology):
    """The set of generated class files must equal the committed set
    (validates root-model-class and non-graph-object class filtering)."""
    generated_names = {
        c.name + '.py'
        for c in core_ontology.classes()
        if generator.should_generate_class(c)
    }
    committed_names = {
        f for f in os.listdir(COMMITTED_CORE_MODEL_DIR)
        if f.endswith('.py') and f not in ('DomainOntology.py', '__init__.py')
    }
    assert generated_names == committed_names


def test_validation_passes_on_core(generator, core_ontology):
    """The committed vital-core ontology must pass §7 validation."""
    generator.validate_ontology(core_ontology, [core_ontology])


def test_all_committed_class_files_parity(generator, core_ontology):
    """Full-corpus byte parity: every committed vital-core class .py/.pyi
    must be reproduced exactly."""
    mismatches = []
    for ont_class in core_ontology.classes():
        if not generator.should_generate_class(ont_class):
            continue
        py = generator.generate_class_code([core_ontology], core_ontology, ont_class)
        if py != read_committed(f'{ont_class.name}.py'):
            mismatches.append(f'{ont_class.name}.py')
        pyi = generator.generate_class_interface_code([core_ontology], core_ontology, ont_class)
        if pyi != read_committed(f'{ont_class.name}.pyi'):
            mismatches.append(f'{ont_class.name}.pyi')
    assert mismatches == []


def test_all_committed_trait_files_parity(generator, core_ontology):
    """Full-corpus byte parity: every committed vital-core trait file must be
    reproduced exactly."""
    mismatches = []
    for ont_prop in core_ontology.properties():
        if not generator.should_generate_trait(core_ontology, ont_prop):
            continue
        trait = generator.generate_property_code(core_ontology, ont_prop)
        if trait != read_committed(f'properties/Property_{ont_prop.name}.py'):
            mismatches.append(f'Property_{ont_prop.name}.py')
    assert mismatches == []
