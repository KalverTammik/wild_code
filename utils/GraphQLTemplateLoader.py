import os
import re
from typing import Optional, Tuple, List, Set
from ..constants.file_paths import QueryPaths
from ..languages.language_manager import LanguageManager

class GraphQLTemplateLoader:
    """
    Loads GraphQL query files with optional fragment imports and a placeholder token.
    - Supports lines like: `# import FragmentName from '../fragments/FragmentName.graphql'`
    - Replaces the token `{{EDGE_FRAGMENT}}` with a provided fragment name (whitelisted).
    - Deduplicates imported fragments by fragment name.
    Does not modify the legacy GraphQLQueryLoader.
    """
    IMPORT_RE = re.compile(r"^\s*#\s*import\s+([A-Za-z0-9_]+)\s+from\s+'([^']+)'\s*$")
    FRAGMENT_NAME_RE = re.compile(r"fragment\s+([A-Za-z0-9_]+)\s+on\s+", re.IGNORECASE)
    FRAGMENT_PLACEHOLDER = "{{EDGE_FRAGMENT}}"

    def __init__(self, lang: Optional[LanguageManager] = None):
        self.lang = lang or LanguageManager()

    def _get_module_folder(self, module: str) -> str:
        """Resolve the absolute folder for a module using QueryPaths, handling legacy typos."""
        attr = module.upper()
        # Legacy alias handling for properties
        if attr == 'PROPERTIES' and not hasattr(QueryPaths, 'PROPERTIES') and hasattr(QueryPaths, 'PROPERTIE'):
            return getattr(QueryPaths, 'PROPERTIE')
        if not hasattr(QueryPaths, attr):
            raise ValueError(self.lang.get("unknown_module").format(module=module))
        return getattr(QueryPaths, attr)

    def _read_file(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _collect_imports(self, base_dir: str, lines: List[str]) -> Tuple[str, List[str]]:
        """Return (base_query_text_without_imports, list_of_imported_fragment_texts)"""
        fragments: List[str] = []
        cleaned_lines: List[str] = []
        for line in lines:
            m = self.IMPORT_RE.match(line)
            if m:
                _, rel_path = m.groups()
                abs_path = os.path.normpath(os.path.join(base_dir, rel_path))
                if os.path.exists(abs_path):
                    fragments.append(self._read_file(abs_path))
                else:
                    # Import not found: {abs_path}
                    pass
            else:
                cleaned_lines.append(line)
        return ("".join(cleaned_lines), fragments)

    def _dedupe_fragments(self, frags: List[str]) -> List[str]:
        seen: Set[str] = set()
        unique: List[str] = []
        for text in frags:
            m = self.FRAGMENT_NAME_RE.search(text)
            name = m.group(1) if m else None
            if name and name not in seen:
                seen.add(name)
                unique.append(text)
        return unique

    def load_with_fragments(self, module: str, filename: str, edge_fragment: Optional[str] = None) -> str:
        """
        Load a query file and resolve imports and placeholder replacement.
        - module: logical module key (e.g., 'PROJECT', 'PROPERTIES', 'USER' or lowercase variants)
        - filename: e.g., 'ListAllProjects.template.graphql'
        - edge_fragment: fragment name to inject for the {{EDGE_FRAGMENT}} placeholder
        Returns the final query string ready for APIClient.
        """
        folder = self._get_module_folder(module)
        query_path = os.path.join(folder, filename)
        if not os.path.exists(query_path):
            raise FileNotFoundError(self.lang.get("query_file_not_found").format(file=query_path))

        base_text = self._read_file(query_path)
        base_dir = os.path.dirname(query_path)
        base_no_imports, imported = self._collect_imports(base_dir, base_text.splitlines(keepends=True))
        imported = self._dedupe_fragments(imported)

        # Safe placeholder replacement
        final_edge_fragment = edge_fragment or ''
        if final_edge_fragment:
            if not re.fullmatch(r"[A-Za-z0-9_]+", final_edge_fragment):
                raise ValueError("Invalid fragment name")
            resolved = base_no_imports.replace(self.FRAGMENT_PLACEHOLDER, final_edge_fragment)
        else:
            # Remove the placeholder token entirely if none provided
            resolved = base_no_imports.replace(self.FRAGMENT_PLACEHOLDER, "")

        return resolved + ("\n\n" + "\n\n".join(imported) if imported else "")
