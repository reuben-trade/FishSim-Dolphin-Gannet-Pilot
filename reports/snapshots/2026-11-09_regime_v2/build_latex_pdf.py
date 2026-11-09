"""Compile and validate the six-page report after render_working_draft.py."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parent
BUNDLE = 'https://data1b.fullyjustified.net/tlextras-2022.0r0.tar'
binary = os.environ.get('FISHSIM_TECTONIC') or shutil.which('tectonic')
if not binary:
    candidate = Path('/tmp/feeding-frenzy-tex-tools/tectonic')
    if candidate.is_file():
        binary = str(candidate)
if not binary:
    raise SystemExit('Install Tectonic or set FISHSIM_TECTONIC to its executable.')

source_hash = hashlib.sha256((ROOT / 'main.tex').read_bytes()).hexdigest()
compiled = ROOT / 'main.pdf'
compiled.unlink(missing_ok=True)
result = subprocess.run(
    [binary, '--bundle', BUNDLE, '--only-cached', '-k', '--keep-logs', 'main.tex'],
    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
(ROOT / 'latex_build_output.log').write_text(result.stdout)
if result.returncode or not compiled.is_file():
    raise SystemExit('LaTeX compilation failed; see latex_build_output.log.')
bad = ('Missing character:', 'Undefined control sequence', 'Overfull ',
       'Citation ', 'undefined references')
if any(marker in result.stdout for marker in bad):
    raise SystemExit('Resolve missing glyphs, references or overflow before publication.')

info = subprocess.check_output(['pdfinfo', str(compiled)], text=True)
if not re.search(r'^Pages:\s+7\s*$', info, re.M):
    raise SystemExit('Expected six body pages and one reference page.')
text = subprocess.check_output(['pdftotext', '-layout', str(compiled), '-'], text=True)
pages = [page for page in text.split('\f') if page.strip()]
content = json.loads((ROOT / 'paper_content_resolved.json').read_text())
def compact(value):
    return ''.join(unicodedata.normalize('NFKC', value).split()).casefold()
for page, expected in zip(pages[:6], content['pages']):
    if compact(expected['heading']) not in compact(page):
        raise SystemExit('Body section moved to an unexpected page.')
if not pages[6].lstrip().startswith('References'):
    raise SystemExit('References must begin on page seven.')
if re.findall(r'Figure\s+([1-4])\s*:', text) != ['1', '2', '3', '4']:
    raise SystemExit('Expected exactly four numbered figure captions.')
if len(re.findall(r'\\bibcite\{', (ROOT / 'main.aux').read_text())) != 8:
    raise SystemExit('Expected the eight verified bibliography entries.')
if hashlib.sha256((ROOT / 'main.tex').read_bytes()).hexdigest() != source_hash:
    raise SystemExit('LaTeX source changed while compiling.')

target = ROOT / 'Feeding_Frenzy_Working_Draft.pdf'
shutil.copy2(compiled, target)
validation = json.loads((ROOT / 'build_validation.json').read_text())
validation.update(renderer='Tectonic LaTeX PDF with BibTeX; editable DOCX companion',
    latex_compiler_network_unavailable=False, latex_source_sha256=source_hash,
    current_pdf_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    compiled_pages=7, references_start_page=7, verified_citations=8,
    numbered_figures_verified=4, missing_glyphs=False, overflow=False)
(ROOT / 'build_validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print('Validated LaTeX PDF: six body pages, four figures, eight references on page seven.')
