from monitorboss.cli import get_help_texts
from monitorboss.impl import Feature
import os


def compile_usage_md_text() -> str:
    help_texts = get_help_texts()
    nl = "\n"  # Python version 3.10 does not allow backslashes inside expression parts of f-strings
    markdown = f'''# Usage

```
{help_texts['']}```

{nl.join(f"""## {sub}
```
{help_texts[sub]}```
""" for sub in help_texts if sub != '')}
## Available attributes
{nl.join(f"""* {attr.name} - {attr.code.description}
  * {attr.code.notes}""" for attr in Feature)}
'''.replace('./scratch.py',
            'monitorboss.py')
    # TODO: convert replace to regex so it doesnt matter where it's called from
    return markdown


def write_to_usage():
    with open(f"{os.getcwd()}/USAGE.md", "w", encoding="utf8") as usage_file:
        usage_file.write(compile_usage_md_text())
