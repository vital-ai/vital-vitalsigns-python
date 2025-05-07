from urllib.parse import urlparse
from typing import Optional

class URIParseError(ValueError):
    """Raised when a graph URI doesn’t conform to the expected patterns."""
    pass

class VitalNameGraph:
    def __init__(self, graph_uri, *,
                 graph_id: str | None = None,
                 account_id: str | None = None,
                 is_global: bool = False):

        self._base_uri = ""
        self._namespace = ""

        self._graph_uri = graph_uri

        self._account_id = account_id
        self._graph_id = graph_id
        self._is_global = is_global

    def get_graph_uri(self):
        return self._graph_uri

    def get_graph_id(self):
        return self._graph_id

    def get_account_id(self):
        return self._account_id

    def get_base_uri(self):
        return self._base_uri

    def get_namespace(self):
        return self._namespace

    def is_global(self):
        return self._is_global

    def to_dict(self) -> dict:
        return {
            "vital_class": "VitalNameGraph",
            "graph_uri": self._graph_uri,
            "base_uri": self._base_uri,
            "namespace": self._namespace,
            "account_id": self._account_id,
            "is_global": self._is_global
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VitalNameGraph":
        """
        Rehydrate a VitalNameGraph from a dict produced by to_dict().
        Expects keys: graph_uri, base_uri, namespace, account_id, is_global, graph_id
        """
        inst = cls(
            data["graph_uri"],
            graph_id=data.get("graph_id"),
            account_id=data.get("account_id"),
            is_global=data.get("is_global", False)
        )
        inst._base_uri = data.get("base_uri", "")
        inst._namespace = data.get("namespace", "")
        return inst

    def __repr__(self):
        return (f"VitalNameGraph(graph_uri={self._graph_uri!r}, "
                f"account_id={self._account_id!r}, "
                f"is_global={self._is_global!r})")

    @classmethod
    def to_uri(cls, *, base_uri: str, namespace: str, graph_id: str, account_id: str|None = None, is_global: bool = False) -> str:

        graph_uri = ""

        if is_global:
            if account_id:
                graph_uri = f"{base_uri}/{namespace}/GLOBAL/{account_id}/{graph_id}"
            else:
                graph_uri = f"{base_uri}/{namespace}/GLOBAL/{graph_id}"
        else:
            if account_id:
                graph_uri = f"{base_uri}/{namespace}/{account_id}/{graph_id}"
            else:
                graph_uri = f"{base_uri}/{namespace}/{graph_id}"

        return graph_uri


    @classmethod
    def from_uri(cls, graph_uri: str) -> "VitalNameGraph":
        """
        Parse a graph URI of the form:
          scheme://host[:port]/<namespace…>/
             graph_id
           | GLOBAL/graph_id
           | account_id/graph_id
           | GLOBAL/account_id/graph_id

        Returns a VitalNameGraph with:
          - _base_uri    = "scheme://host[:port]"
          - _namespace   = all path segments between host and the first of GLOBAL/account_id
          - _is_global   = True if GLOBAL was present
          - _account_id  = the account_id (None if absent)
          - _graph_id    = the final segment
        """
        # 1) Extract scheme://host[:port]
        p = urlparse(graph_uri)
        if not (p.scheme and p.netloc):
            raise URIParseError(f"URI must include scheme and host: {graph_uri!r}")
        base_uri = f"{p.scheme}://{p.netloc}"

        # 2) Split the path into non-empty segments
        segments = [seg for seg in p.path.split("/") if seg]
        if len(segments) < 2:
            raise URIParseError(f"URI must have at least namespace and graph_id: {segments!r}")

        # 3) Identify graph_id (last segment) — must not be "GLOBAL"
        graph_id = segments[-1]
        if graph_id == "GLOBAL":
            raise URIParseError("'GLOBAL' cannot be used as graph_id")

        is_global = False
        account_id: Optional[str] = None

        # 4) Peel off trailing patterns in order:
        #    a) …/<ns…>/GLOBAL/account_id/graph_id
        #    b) …/<ns…>/GLOBAL/graph_id
        #    c) …/<ns…>/account_id/graph_id
        if len(segments) >= 3 and segments[-3] == "GLOBAL":
            # Pattern a)
            is_global = True
            account_id = segments[-2]
            if account_id == "GLOBAL":
                raise URIParseError("'GLOBAL' cannot be used as account_id")
            namespace_segs = segments[:-3]

        elif segments[-2] == "GLOBAL":
            # Pattern b)
            is_global = True
            account_id = None
            namespace_segs = segments[:-2]

        else:
            # Pattern c)
            is_global = False
            account_id = segments[-2]
            if account_id == "GLOBAL":
                raise URIParseError("'GLOBAL' cannot be used as account_id")
            namespace_segs = segments[:-2]

        # 5) Reconstruct namespace (must not be empty)
        namespace = "/".join(namespace_segs)
        if not namespace:
            raise URIParseError(f"Namespace cannot be empty: {graph_uri!r}")

        # 6) Instantiate and populate
        inst = cls(graph_uri,
                   graph_id=graph_id,
                   account_id=account_id,
                   is_global=is_global)
        inst._base_uri = base_uri
        inst._namespace = namespace
        return inst

