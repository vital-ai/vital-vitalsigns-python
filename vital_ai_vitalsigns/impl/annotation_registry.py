KNOWN_ANNOTATION_URIS = frozenset({
    'http://www.w3.org/2000/01/rdf-schema#label',
    'http://www.w3.org/2000/01/rdf-schema#comment',
    'http://www.w3.org/2000/01/rdf-schema#seeAlso',
    'http://www.w3.org/2000/01/rdf-schema#isDefinedBy',
    'http://www.w3.org/2002/07/owl#versionInfo',
    'http://www.w3.org/2002/07/owl#deprecated',
})

# Mutable set for runtime-registered custom annotation URIs
_custom_annotation_uris = set()


def is_annotation_property(uri: str) -> bool:
    return uri in KNOWN_ANNOTATION_URIS or uri in _custom_annotation_uris


def register_annotation_property(uri: str):
    _custom_annotation_uris.add(uri)


def unregister_annotation_property(uri: str):
    _custom_annotation_uris.discard(uri)
