from monitorboss.cli import get_help_texts
from monitorboss.impl import Attribute
import os


def compile_usage_md_text() -> str:
    help_texts = get_help_texts()
    markdown = f'''# Usage

```
{help_texts['']}```

{"\n".join(f"""## {sub}
```
{help_texts[sub]}```
""" for sub in help_texts if sub != '')}
## Available attributes
{'\n'.join(f"""* {attr.name.lower()} - {attr.value.description}
  * {attr.value.notes}""" for attr in Attribute)}
'''.replace('./scratch.py', 'monitorboss.py')  # TODO: convert replace to regex so it doesnt matter where its called from

    return markdown


def write_to_usage():
    with open(f"{os.getcwd()}/USAGE.md", "w", encoding="utf8") as usagefile:
        usagefile.write(compile_usage_md_text())
