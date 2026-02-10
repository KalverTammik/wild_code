import ast
import os
import re
import yaml
from collections import defaultdict, Counter
from difflib import SequenceMatcher

# --- CONFIG ---
TRANSLATION_KEYS_PATH = 'languages/translation_keys.py'
EN_PATH = 'languages/en.py'
ET_PATH = 'languages/et.py'
REPORT_PATH = 'reports/translations_similarity_report.md'
MERGE_PLAN_PATH = 'config/translation_merge_plan.yaml'

# --- UTILS ---
def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('...', '…')
    text = re.sub(r'[\.:;!?]$', '', text)
    return text

def fuzzy_match(a, b):
    return SequenceMatcher(None, a, b).ratio() >= 0.88

# --- 1. Translation Inventory ---
def parse_translation_keys(path):
    with open(path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=path)
    inventory = defaultdict(list)
    duplicates = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            seen = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            value = ast.literal_eval(item.value)
                            key = f'{node.name}.{name}'
                            inventory[key].append({'class': node.name, 'name': name, 'value': value})
                            if name in seen:
                                duplicates.append(f'{node.name}.{name}')
                            seen.add(name)
    return inventory, duplicates

def parse_translations_dict(path):
    with open(path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=path)
    translations = []
    duplicates = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'TRANSLATIONS':
                    dict_node = node.value
                    if isinstance(dict_node, ast.Dict):
                        seen = set()
                        for k, v in zip(dict_node.keys, dict_node.values):
                            key_repr = ast.unparse(k)
                            value_repr = ast.literal_eval(v)
                            translations.append((key_repr, value_repr))
                            if key_repr in seen:
                                duplicates.append(key_repr)
                            seen.add(key_repr)
    return translations, duplicates

def build_inventory():
    keys_inv, keys_dupes = parse_translation_keys(TRANSLATION_KEYS_PATH)
    en_trans, en_dupes = parse_translations_dict(EN_PATH)
    et_trans, et_dupes = parse_translations_dict(ET_PATH)
    table = defaultdict(lambda: {'en': None, 'et': None, 'origins': []})
    for k, v in en_trans:
        table[k]['en'] = v
        table[k]['origins'].append('en')
    for k, v in et_trans:
        table[k]['et'] = v
        table[k]['origins'].append('et')
    for k in keys_inv:
        for entry in keys_inv[k]:
            table[k]['origins'].append('translation_keys')
    return table, keys_dupes, en_dupes, et_dupes

# --- 2. Find Usage Locations ---
def find_usages(key_reprs):
    usage_counts = defaultdict(int)
    usage_files = defaultdict(list)
    patterns = [r'translate\s*\(', r'tr\s*\(', r'get_translation', r'TRANSLATIONS\s*\[']
    for root, dirs, files in os.walk('.'):
        for fname in files:
            if fname.endswith('.py'):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    continue
                for key in key_reprs:
                    if key in content:
                        usage_counts[key] += content.count(key)
                        usage_files[key].append(fpath)
    return usage_counts, usage_files

# --- 3. Similarity Grouping ---
def cluster_translations(table):
    clusters = []
    norm_map = defaultdict(list)
    for key, entry in table.items():
        en_val = entry['en']
        if en_val:
            norm = normalize_text(en_val)
            norm_map[norm].append((key, en_val, entry['et']))
    # Stage A: Exact match
    for norm, members in norm_map.items():
        clusters.append({'norm': norm, 'members': members, 'type': 'AUTO_SAFE'})
    # Stage B/C: Fuzzy
    fuzzy_clusters = []
    all_norms = list(norm_map.keys())
    for i, norm1 in enumerate(all_norms):
        for j, norm2 in enumerate(all_norms):
            if i < j and fuzzy_match(norm1, norm2):
                fuzzy_clusters.append({'norms': [norm1, norm2], 'members': norm_map[norm1]+norm_map[norm2], 'type': 'NEEDS_REVIEW'})
    return clusters, fuzzy_clusters

# --- 4. Canonical ID Naming ---
def propose_canonical_id(key):
    if '.' in key:
        return key.lower()
    return f'common.{key.lower()}'

# --- 5. Output Artifacts ---
def write_report(table, clusters, fuzzy_clusters, keys_dupes, en_dupes, et_dupes):
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('# Translation Similarity Report\n\n')
        f.write('## Duplicate Constants in translation_keys.py\n')
        for d in keys_dupes:
            f.write(f'- {d}\n')
        f.write('\n## Duplicate Dict Keys in en.py\n')
        for d in en_dupes:
            f.write(f'- {d}\n')
        f.write('\n## Duplicate Dict Keys in et.py\n')
        for d in et_dupes:
            f.write(f'- {d}\n')
        f.write('\n## Clusters (AUTO_SAFE)\n')
        for c in clusters:
            f.write(f'- Norm: {c["norm"]}\n')
            for m in c['members']:
                f.write(f'  - {m[0]}: EN="{m[1]}" ET="{m[2]}"\n')
            f.write('\n')
        f.write('\n## Clusters (NEEDS_REVIEW)\n')
        for c in fuzzy_clusters:
            f.write(f'- Norms: {c["norms"]}\n')
            for m in c['members']:
                f.write(f'  - {m[0]}: EN="{m[1]}" ET="{m[2]}"\n')
            f.write('\n')

    # YAML merge plan
    merge_plan = []
    for c in clusters:
        canonical_id = propose_canonical_id(c['members'][0][0])
        merge_plan.append({
            'cluster_id': c['norm'],
            'canonical_id': canonical_id,
            'members': [m[0] for m in c['members']],
            'chosen_en': c['members'][0][1],
            'chosen_et': c['members'][0][2],
            'status': c['type'],
            'notes': ''
        })
    for c in fuzzy_clusters:
        canonical_id = propose_canonical_id(c['members'][0][0])
        merge_plan.append({
            'cluster_id': ','.join(c['norms']),
            'canonical_id': canonical_id,
            'members': [m[0] for m in c['members']],
            'chosen_en': c['members'][0][1],
            'chosen_et': c['members'][0][2],
            'status': c['type'],
            'notes': 'REVIEW FUZZY MATCHES'
        })
    with open(MERGE_PLAN_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(merge_plan, f, allow_unicode=True)

# --- MAIN ---
def main():
    table, keys_dupes, en_dupes, et_dupes = build_inventory()
    usage_counts, usage_files = find_usages(list(table.keys()))
    clusters, fuzzy_clusters = cluster_translations(table)
    write_report(table, clusters, fuzzy_clusters, keys_dupes, en_dupes, et_dupes)
    print('Translation audit complete. See reports/translations_similarity_report.md and config/translation_merge_plan.yaml.')

if __name__ == '__main__':
    main()
