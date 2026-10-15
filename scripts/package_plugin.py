"""Build a skills-only Agent Plugins package from the maintained physwhen skill."""
import argparse
import json
from pathlib import Path
import re
import zipfile

try:
    from scripts.package_skill import FILES
except ModuleNotFoundError:
    from package_skill import FILES

SCHEMA = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'


def plugin_payload(base):
    base = Path(base)
    manifest = json.loads((base / 'plugin.json').read_text())
    if manifest.get('$schema') != SCHEMA or manifest.get('name') != 'physwhen':
        raise ValueError('Expected the portable physwhen manifest')
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', manifest.get('version', '')):
        raise ValueError('Expected a numeric SemVer package revision')
    if set(manifest) - {'$schema', 'name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords', 'extensions'}:
        raise ValueError('Unsupported manifest fields; this package is skills-only')
    interface = manifest['extensions']['com.openai']['interface']
    if set(manifest['extensions']) != {'com.openai'} or set(manifest['extensions']['com.openai']) != {'interface'}:
        raise ValueError('Unexpected plugin dependencies or restrictions')
    if not 1 <= len(interface['shortDescription']) <= 30:
        raise ValueError('Plugin shortDescription must contain 1–30 characters')
    if interface.get('capabilities') != []:
        raise ValueError('No tools or interactive views are provided')
    prompts = interface.get('defaultPrompt')
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or not all(isinstance(p, str) and p.strip() for p in prompts):
        raise ValueError('Expected one to three nonempty default prompts')
    paths = ['plugin.json', 'LICENSE'] + ['skills/physwhen/' + f for f in FILES]
    payload = {}
    for name in paths:
        path = base / name
        if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
            raise ValueError('Plugin resource escapes package: ' + name)
        payload[name] = path.read_bytes()
    if payload['LICENSE'] != payload['skills/physwhen/LICENSE']:
        raise ValueError('Root and skill licenses differ')
    if b'\nname: physwhen\n' not in payload['skills/physwhen/SKILL.md']:
        raise ValueError('Skill name does not match its directory')
    # Check bundled Markdown links without assuming a host can read the research workspace.
    for name, data in payload.items():
        if not name.endswith('.md'):
            continue
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', data.decode()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            resolved = (base / name).parent.joinpath(target.split('#')[0]).resolve()
            if not resolved.is_relative_to(base.resolve()) or str(resolved.relative_to(base.resolve())) not in payload:
                raise ValueError('Unbundled skill reference: ' + target)
    return payload


def package(base, output, check=False):
    payload = plugin_payload(base)
    output = Path(output)
    if check:
        with zipfile.ZipFile(output) as archive:
            if len(archive.namelist()) != len(payload) or set(archive.namelist()) != set(payload):
                raise ValueError('Unexpected plugin archive members')
            for name, data in payload.items():
                if archive.read(name) != data:
                    raise ValueError('Plugin archive differs from source: ' + name)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in payload.items():
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data)
        temporary.replace(output)
    return len(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[1]
    count = package(base, base / 'deliverables/PhysWhen-plugin.zip', args.check)
    print(('Verified' if args.check else 'Built') + f' PhysWhen plugin: {count} files; host execution not implied.')
