from rdflib import URIRef, BNode, Literal


class VirtuosoUtils:

    @classmethod
    def format_as_ntriples(cls, s, p, o, o_type, o_datatype=None, o_lang=None):

        s_uri = URIRef(s)
        p_uri = URIRef(p)

        if o_type == "uri":
            o_uri = URIRef(o)
        elif o_type == "bnode":
            o_uri = BNode(o)
        elif o_type == "literal" and o_datatype:
            # If datatype is provided, include it
            o_uri = Literal(o, datatype=URIRef(o_datatype))
        elif o_type == "literal" and o_lang:
            # If language is provided, include it
            o_uri = Literal(o, lang=o_lang)
        else:
            # Plain literal
            o_uri = Literal(o)

        # Format as N-Triples
        return f"{s_uri.n3()} {p_uri.n3()} {o_uri.n3()} .\n"


