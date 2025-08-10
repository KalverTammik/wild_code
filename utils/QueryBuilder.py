from typing import Dict, Optional, Tuple
from .GraphQLTemplateLoader import GraphQLTemplateLoader

class QueryBuilder:
    """
    Opt-in, module-based query constructor.
    Keeps legacy loaders intact. Use when you want fragment selection and templated queries.
    """
    def __init__(self, lang=None):
        self.loader = GraphQLTemplateLoader(lang=lang)

    def list(self, module: str, template_filename: str, edge_fragment: str, variables: Optional[Dict] = None) -> Tuple[str, Dict]:
        query = self.loader.load_with_fragments(module, template_filename, edge_fragment=edge_fragment)
        return query, (variables or {})

    def detail(self, module: str, template_filename: str, edge_fragment: str, id_value: str, variables: Optional[Dict] = None) -> Tuple[str, Dict]:
        vars_final = dict(variables or {})
        # Common pattern: id variable
        if 'id' not in vars_final:
            vars_final['id'] = id_value
        query = self.loader.load_with_fragments(module, template_filename, edge_fragment=edge_fragment)
        return query, vars_final
