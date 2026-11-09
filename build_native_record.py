"""Record a separately built native module and its complete unchanged sources."""
from pathlib import Path
import hashlib
import json
import platform
import shutil
import subprocess
import sys

source, build, destination = map(Path, sys.argv[1:4])
destination.mkdir(parents=True, exist_ok=True)
configure_command = [
    'cmake', '-S', str(source), '-B', str(build), '-G', 'Ninja',
    '-DCMAKE_BUILD_TYPE=Release', '-DPython_EXECUTABLE=' + sys.executable,
    '-DPYTHON_EXECUTABLE=' + sys.executable, '-DPYBIND11_FINDPYTHON=ON',
    '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
]
build_command = ['cmake', '--build', str(build), '--target', 'cmodel',
                 '--parallel', '1', '--verbose']
subprocess.run(configure_command, check=True)
subprocess.run(build_command, check=True)
binaries = list(build.glob('cmodel*.so'))
if len(binaries) != 1:
    raise SystemExit('Expected one Linux CPython native module.')
binary = binaries[0]
files = [source / 'CMakeLists.txt']
for name in ('src', 'extern'):
    files.extend(p for p in (source / name).rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts and p.suffix != '.pyc')
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copy2(binary, destination / binary.name)
cache = (build / 'CMakeCache.txt').read_text()
compiler_path = next(line.split('=', 1)[1] for line in cache.splitlines()
                     if line.startswith('CMAKE_CXX_COMPILER:FILEPATH='))
compile_commands = json.loads((build / 'compile_commands.json').read_text())
generated_commands = subprocess.check_output(
    ['ninja', '-C', str(build), '-t', 'commands'], text=True)
shutil.copy2(build / 'compile_commands.json', destination / 'compile_commands.json')
shutil.copy2(build / 'CMakeCache.txt', destination / 'CMakeCache.txt')
(destination / 'generated_commands.txt').write_text(generated_commands)
record = dict(status='built_not_execution_validated', python_version=platform.python_version(),
    platform=platform.platform(), binary_filename=binary.name, binary_sha256=digest(binary),
    model_source_sha256={str(p.relative_to(source)): digest(p) for p in sorted(files)},
    compiler_path=compiler_path,
    compiler=subprocess.check_output([compiler_path, '--version'], text=True).splitlines()[0],
    cmake=subprocess.check_output(['cmake', '--version'], text=True).splitlines()[0],
    configure_command=configure_command, build_command=build_command,
    compile_workers=1, compile_commands=compile_commands,
    generated_compile_and_link_commands=generated_commands,
    build_evidence_sha256={name:digest(destination / name) for name in
        ('CMakeCache.txt', 'compile_commands.json', 'generated_commands.txt')},
    cache=cache, native_steps=0,
    interpretation='New source-built module; distinct from the historical pinned binary. Runtime validation is separate.')
(destination / 'NATIVE_BUILD.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded candidate native module', binary.name, record['binary_sha256'])
