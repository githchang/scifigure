#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    root=Path(__file__).resolve().parents[1]
    skill=root/'SKILL.md'
    errors=[]
    if not skill.exists():
        errors.append('SKILL.md is missing')
    else:
        text=skill.read_text(encoding='utf-8')
        if not text.startswith('---\n'):
            errors.append('SKILL.md must start with YAML frontmatter')
        parts=text.split('---',2)
        if len(parts)<3:
            errors.append('SKILL.md frontmatter is not closed')
        else:
            fm=parts[1]
            name_match=re.search(r'^name:\s*([^\n]+)$',fm,re.M)
            desc_match=re.search(r'^description:\s*([^\n]+)$',fm,re.M)
            if not name_match: errors.append('frontmatter name is missing')
            else:
                name=name_match.group(1).strip()
                if not re.fullmatch(r'[a-z0-9-]{1,64}',name): errors.append(f'invalid skill name: {name}')
                if root.name.lower()!=name:
                    errors.append(f'skill folder should be named {name}; current folder is {root.name}')
            if not desc_match: errors.append('frontmatter description is missing')
    required=[root/'agents'/'openai.yaml',root/'scripts'/'scifigure.py',root/'references'/'custom-input.md',root/'references'/'styles.md',root/'examples'/'demo_ir.json',root/'README.md']
    for p in required:
        if not p.exists(): errors.append(f'missing required file: {p.relative_to(root)}')
    if errors:
        print('\n'.join('ERROR: '+e for e in errors),file=sys.stderr)
        return 1
    print('SciFigure skill structure is valid.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
