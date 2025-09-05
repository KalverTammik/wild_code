import os
from typing import Optional
from ..constants.file_paths import QueryPaths  # This should be defined in file_paths.py for all query folders
from ..languages.language_manager import LanguageManager

class GraphQLQueryLoader:
    """
    Loads GraphQL query files by module and query name, using only paths from QueryPaths.
    All error messages use translation keys.
    """
    def __init__(self, lang: Optional[LanguageManager] = None):
        self.lang = lang or LanguageManager()

    def load_query(self, module: str, query_filename: str) -> str:
        """
        Load a .graphql query file for a given module and query name.
        Args:
            module (str): The module name (must match a key in QueryPaths).
            query_filename (str): The .graphql filename (e.g., 'me.graphql').
        Returns:
            str: The contents of the query file.
        Raises:
            FileNotFoundError: If the query file does not exist.
            ValueError: If the module is unknown.
        """
        #print(f"[method load_query] Loading query for module: {module}, filename: {query_filename}")
        if not hasattr(QueryPaths, module.upper()):
            raise ValueError(self.lang.translate("unknown_module").format(module=module))
        folder = getattr(QueryPaths, module.upper())
        #print(f"[method load_query] Query folder found: {folder}")
        query_path = os.path.join(folder, query_filename)
        #print(f"[method load_query] Loading GraphQL query from: {query_path}")  # Debug log
        #print(f"[method load_query] Query file exists: {os.path.exists(query_path)}")
        if not os.path.exists(query_path):
            raise FileNotFoundError(self.lang.translate("query_file_not_found").format(file=query_path))
        with open(query_path, 'r', encoding='utf-8') as f:
            return f.read()

# Example QueryPaths (to be defined in constants/file_paths.py):
# class QueryPaths:
#     USER = 'queries/graphql/user'
#     PROJECT = 'queries/graphql/projects'
#     ...

# Translation keys to add:
# "unknown_module": "Unknown module: {module}"
# "query_file_not_found": "Query file not found: {file}"
