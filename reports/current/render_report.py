"""Render the V3 manuscript only; no simulation or analysis execution."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parent
d=json.loads((R/'manuscript.json').read_text())
blocks=d['blocks'];refs=d['references'];title=d['title']
(R/'manuscript.txt').write_text('\n\n'.join(b['text'] if b['kind']!='figure' else 'Figure '+str(b['number'])+'. '+b['caption'] for b in blocks)+'\n\nReferences\n\n'+'\n\n'.join(refs)+'\n')
(R/'captions.json').write_text(json.dumps({b['name']:b['caption'] for b in blocks if b['kind']=='figure'},ensure_ascii=False,indent=2)+'\n')
KEYS={1:'teske2021',2:'odonoghue2009',3:'lett2014',4:'thiebault2016',5:'couzin2002',6:'ropert2004',7:'mohapatra2025',8:'licht2026',9:'stockin2022',10:'sanbi2018'}
def tex(t):
 t=t.replace('’',"'").replace('–','--').replace('−','-').replace('→',r'\ensuremath{\rightarrow}').replace('π',r'\ensuremath{\pi}').replace('×',r'\ensuremath{\times}').replace('≈',r'\ensuremath{\approx}')
 urls={}
 def url(m):
  key=f'URLTOKEN{len(urls)}END';x=m[0].rstrip(';.,');urls[key]=r'\url{'+x+'}'+m[0][len(x):];return key
 t=re.sub(r'https://[^\s]+',url,t)
 for a,b in [('%',r'\%'),('&',r'\&'),('_',r'\_'),('#',r'\#')]:t=t.replace(a,b)
 t=re.sub(r'\[((?:10|[1-9])(?:,(?:10|[1-9]))*)\]',lambda m:r'\citep{'+','.join(KEYS[int(x)] for x in m[1].split(','))+'}',t)
 t=re.sub(r'Figure ([1-4])([a-d](?:,[a-d])?)?',lambda m:r'Figure~\ref{fig:'+m[1]+'}'+(m[2] or ''),t)
 for k,v in urls.items():t=t.replace(k,v)
 return t
parts=[r'\documentclass[10pt,a4paper,twocolumn]{article}',r'\usepackage[margin=18mm,columnsep=6mm]{geometry}',r'\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}',r'\usepackage{mathptmx,microtype,graphicx,amsmath,caption}',r'\usepackage[numbers,sort&compress]{natbib}\usepackage[hidelinks]{hyperref}\usepackage{xurl}',r'\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}\setlength{\bibsep}{3pt}',r'\captionsetup{font=small,labelfont=bf,skip=4pt}',r'\renewcommand{\dbltopfraction}{.9}\renewcommand{\textfraction}{.05}\renewcommand{\dblfloatpagefraction}{.8}\setcounter{dbltopnumber}{2}',r'\title{'+tex(title)+'}',r'\author{Reuben Stanley\\University of Western Australia}',r'\date{10 November 2026 | Working draft V3 (updated)}',r'\begin{document}\raggedbottom',r'\twocolumn[\maketitle\begin{center}\begin{minipage}{0.97\textwidth}\textbf{Abstract.} '+tex(blocks[3]['text'])+r'\par\vspace{8pt}\end{minipage}\end{center}]']
for b in blocks[4:]:
 k,t=b['kind'],b['text']
 if k=='section':parts.append(r'\section{'+tex(t)+'}')
 elif k=='subsection':parts.append(r'\subsection{'+tex(t)+'}')
 elif k=='p':parts.append(tex(t)+'\n')
 elif k=='figure':parts.append(r'\begin{figure*}[!t]\centering\includegraphics[width=\textwidth]{figures/'+b['name']+r'.pdf}\caption{'+tex(b['caption'])+r'}\label{fig:'+str(b['number'])+r'}\end{figure*}')
parts.append(r'\begin{thebibliography}{10}')
for i,ref in enumerate(refs,1):parts.append(r'\bibitem{'+KEYS[i]+'} '+tex(re.sub(r'^\[\d+\] ','',ref)))
parts.extend([r'\end{thebibliography}',r'\end{document}'])
(R/'main.tex').write_text('\n'.join(parts)+'\n')
print('Rendered V3 source from manuscript.json; '+str(sum(len(b['text'].split()) for b in blocks))+' body words.')
