"""Native bitmap mapping against the same Unicode font, current role fixtures."""
import configparser
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
fixtures = {'DomainOS': root/'colors/DomainOS-SR10.4.colors',
            'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
            'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors')}
rows = []
for name in ('DomainOS', 'BreezeLight', 'BreezeDark', 'TestYellow'):
    if name == 'TestYellow':
        # Artificial palette fixture; never installed into an application.
        roles = {'face': '#ecd870', 'text': '#201c0c'}
    else:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        if not fixtures[name].exists():
            raise SystemExit('Missing native palette fixture: '+str(fixtures[name]))
        parser.read(fixtures[name])
        roles = {key: '#%02x%02x%02x'%tuple(map(int, parser['Colors:Window'][role].split(',')))
                 for key, role in (('face', 'BackgroundNormal'), ('text', 'ForegroundNormal'))}
    assert roles['face'] != roles['text']
    result = subprocess.run([sys.argv[1], roles['face'], roles['text']],
                            text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise RuntimeError(result.stdout+result.stderr)
    samples = [line for line in result.stdout.splitlines() if line.startswith('sample=')]
    assert len(samples) == 5
    assert all('direct-vs-utf8=0 direct-vs-mb=0' in line for line in samples)
    rows.append({'name': name, 'roles': roles, 'samples': samples,
                 'stderr': result.stderr, 'terminal': result.returncode})
print(json.dumps({'scope': 'FontSet UTF8/MB vs direct Unicode glyph pixels, four role palettes; not widget state or all languages',
                  'status': 'passed', 'rows': rows}, ensure_ascii=False, indent=2))
