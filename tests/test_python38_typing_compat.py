from pathlib import Path
import re


def test_no_python310_union_none_typing():
    targets = [Path('main.py')]
    targets.extend(Path('src').glob('*.py'))
    targets.extend(p for p in Path('tests').glob('*.py') if p.name != 'test_python38_typing_compat.py')

    pattern = re.compile(r"\|\s*" + "None" + r"|" + "None" + r"\s*\|")
    hits = []
    for path in targets:
        text = path.read_text(encoding='utf-8')
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{path}:{lineno}:{line.strip()}")

    assert not hits, "Found Python 3.10+ union-with-None typing:\n" + "\n".join(hits)
