"""Smoke-test the installed console entry point, not a source-path import."""
from pathlib import Path
import os
import subprocess
import sysconfig

root = Path(__file__).resolve().parents[1]
cli = Path(sysconfig.get_path('scripts')) / ('aion.exe' if os.name == 'nt' else 'aion')
for path in sorted((root / 'examples').glob('*.aion')):
    expected = 1 if path.name.startswith('negative-') else 0
    result = subprocess.run([str(cli), str(path)], capture_output=True, text=True)
    assert result.returncode == expected, (path.name, result.stdout, result.stderr)
    if expected:
        count = 6 if 'dangling' in path.name else 2
        assert f'{count} semantic error(s)' in result.stderr, result.stderr
        result = subprocess.run([str(cli), str(path), '--no-validate'], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
for args, expected in [(['--help'], 0), (['--unknown'], 2), ([str(root/'examples'/'missing.aion')], 1)]:
    result = subprocess.run([str(cli), *args], capture_output=True, text=True)
    assert result.returncode == expected, result.stderr
print('Installed CLI: four positive specs, two exact negative diagnostic sets, parse-only and usage checks passed.')
