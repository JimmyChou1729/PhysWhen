"""Build or verify the single portable physwhen package; no corpus access required."""
import argparse
from pathlib import Path
import zipfile

FILES = (
    'SKILL.md', 'profile.json', 'LICENSE',
    'references/structure-evidence.md', 'references/structure-source-anchors.jsonl',
    'references/local-evidence.md', 'references/local-source-anchors.jsonl',
    'references/outline-contract.md', 'references/evidence-workflow.md', 'scripts/check_outline.py',
)


def package(root, output, check=False):
    root, output = Path(root), Path(output)
    payload = {}
    for name in FILES:
        source = root / name
        if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError('Skill resource escapes its directory: ' + name)
        payload['physwhen/' + name] = source.read_bytes()
    if b'\nname: physwhen\n' not in payload['physwhen/SKILL.md']:
        raise ValueError('Expected the stable skill name physwhen')
    if check:
        with zipfile.ZipFile(output) as archive:
            if len(archive.namelist()) != len(payload) or set(archive.namelist()) != set(payload):
                raise ValueError('Unexpected package members')
            for name, content in payload.items():
                if archive.read(name) != content:
                    raise ValueError('Package differs from source: ' + name)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in payload.items():
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, content)
        temporary.replace(output)
    return len(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the existing ZIP without writing it')
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[1]
    if (base / 'LICENSE').read_bytes() != (base / 'skills/physwhen/LICENSE').read_bytes():
        raise SystemExit('Root and portable skill licenses differ')
    count = package(base / 'skills/physwhen', base / 'deliverables/PhysWhen-skill.zip', args.check)
    print(('Verified' if args.check else 'Built') + f' physwhen: {count} portable files. No scientific or readability validation implied.')
