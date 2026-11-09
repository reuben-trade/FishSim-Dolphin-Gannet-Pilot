"""Create a small source-only build context; never copy datasets or credentials."""
from pathlib import Path
import argparse
import shutil
from current_runtime import native_source_files, write, reject_source_destination

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
package, output = args.package_root.resolve(), args.output.resolve()
reject_source_destination(output, [package / 'frozen_model'])
source_hashes = native_source_files(package)
if output.exists():
    parser.error('Build context must be a fresh directory.')
output.mkdir(parents=True)
here = Path(__file__).resolve().parent
for name in ('Dockerfile.runtime', 'requirements-runtime-container.txt', 'build_native_record.py'):
    shutil.copy2(here / name, output / name)
source = package / 'frozen_model'
(output / 'frozen_model').mkdir()
shutil.copy2(source / 'CMakeLists.txt', output / 'frozen_model/CMakeLists.txt')
for directory in ('src', 'extern'):
    shutil.copytree(source / directory, output / 'frozen_model' / directory,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
write(output / 'BUILD_CONTEXT_INPUTS.json', dict(status='source_context_only', native_steps=0,
    model_source_sha256=source_hashes,
    excluded=['data/', 'outputs/', 'work/', '.git/', 'historical native binary']))
print(output)
