"""
OML Query Adapter

Loads canonical .sparql files directly from disk and executes them
via an injected query executor.
"""

from pathlib import Path
import inspect


class OmlQueryAdapter:
    def __init__(self, query_executor=None, sparql_dir="src/method/sparql"):
        self.query_executor = query_executor
        self.sparql_dir = Path(sparql_dir)

    def load_query(self, name: str) -> str:
        filename = name if name.endswith(".sparql") else f"{name}.sparql"
        path = self.sparql_dir / filename
        if not path.is_file():
            # We might also try relative to this file location -- that's reasonable
            alt_path = Path(__file__).parent.parent / "sparql" / filename
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"SPARQL query file not found: {path} (or {alt_path})")
        return path.read_text(encoding="utf-8").strip()

    async def execute(self, query_name: str, **kwargs):
        if self.query_executor is None:
            raise RuntimeError("No query executor provided!  I don't know how to execute this query!  AHHHHH!")
        sparql_text = self.load_query(query_name)
        result = self.query_executor(sparql_text, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
