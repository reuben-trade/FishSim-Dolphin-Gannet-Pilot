from pathlib import Path
import json, textwrap, zipfile, html, hashlib, re
from datetime import datetime
from zoneinfo import ZoneInfo
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath
from PIL import Image

ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'paper_content.json').read_text())
summary='The follow-up tests produced 87 captures alone and 101 with gannets, a descriptive increase of 16.1%. The paired counts were 23 to 24 and 20 to 24 in new school 1, and 22 to 23 and 22 to 30 in new school 2. School-average gains were 2.5 and 4.5 fish. All four repetitions were positive, but they represent only two independent new schools.'
verdict='The follow-up tests showed a positive effect of adding gannets in both school averages and all four repetitions. This strengthens the development signal under this fixed model; it does not establish statistical generality or reciprocal benefits to gannets.'
for page in d['pages']:
 page['paragraphs']=[[h,t.replace('REPLICATION_RESULT',summary).replace('REPLICATION_VERDICT',verdict)] for h,t in page['paragraphs']]
(ROOT/'paper_content_resolved.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
W,H=595.276,841.89;M=51.024;G=17.008;CW=(W-2*M-G)/2
normal=FontProperties(family='Liberation Serif',size=10)
bold=FontProperties(family='Liberation Serif',size=10,weight='bold')
measure=TextToPath()
def wrap(s,width=CW,prop=normal):
 words=s.split();lines=[];line=''
 for word in words:
  trial=(line+' '+word).strip()
  if line and measure.get_text_width_height_descent(trial,prop,False)[0]>width:
   lines.append(line);line=word
  else:line=trial
 if line:lines.append(line)
 return lines

def newpage():
 fig=plt.figure(figsize=(W/72,H/72));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,W);ax.set_ylim(0,H);ax.axis('off');return fig,ax
def put(ax,x,y,text,prop=normal):ax.text(x,y,text,fontproperties=prop,va='top',ha='left',color='black')
def layout(page,index):
 fig,ax=newpage();y=H-M;columns=[[],[]]
 if index==0:
  title=textwrap.wrap(d['title'],66)
  for t in title:put(ax,M,y,t,FontProperties(family='Liberation Serif',size=17,weight='bold'));y-=20
  put(ax,M,y-2,d['author'],FontProperties(family='Liberation Serif',size=10));y-=18
  put(ax,M,y,d['date'],FontProperties(family='Liberation Serif',size=9));y-=22
 put(ax,M,y,page['heading'],FontProperties(family='Liberation Serif',size=12,weight='bold'));y-=22
 if 'figure' in page:
  path=ROOT/'figures'/(page['figure']+'.png');im=Image.open(path);height=(W-2*M)*im.height/im.width
  a=fig.add_axes([M/W,(y-height)/H,(W-2*M)/W,height/H]);a.imshow(im);a.axis('off');y-=height+5
  caption='Figure '+str(index)+'. '+page['caption']
  cp=FontProperties(family='Liberation Serif',size=8.5)
  for line in wrap(caption,W-2*M,cp):put(ax,M,y,line,cp);y-=10
  y-=10
 top=y;paragraphs=page['paragraphs']
 costs=[14+len(wrap(text))*12+5 for heading,text in paragraphs]
 available=top-M-12
 feasible=[(max(sum(costs[:k]),sum(costs[k:])),abs(sum(costs[:k])-sum(costs[k:])),k) for k in range(1,len(paragraphs)) if max(sum(costs[:k]),sum(costs[k:]))<=available]
 if not feasible:raise RuntimeError(f'Page {index+1} cannot fit at required font and margins')
 split=min(feasible)[2]
 columns=[paragraphs[:split],paragraphs[split:]]
 for col,items in enumerate(columns):
  y=top;x=M+col*(CW+G)
  for heading,text in items:
   put(ax,x,y,heading,bold);y-=14
   for line in wrap(text):put(ax,x,y,line);y-=12
   y-=5
 put(ax,W/2-3,27,str(index+1),FontProperties(family='Liberation Serif',size=9))
 return fig,columns

layouts=[];pdf=ROOT/'Feeding_Frenzy_Working_Draft.pdf'
with PdfPages(pdf) as out:
 for i,page in enumerate(d['pages']):
  fig,cols=layout(page,i);out.savefig(fig);plt.close(fig);layouts.append(cols)
 fig,ax=newpage();y=H-M;put(ax,M,y,'References',FontProperties(family='Liberation Serif',size=12,weight='bold'));y-=24
 col=0;top=y
 for ref in d['references']:
  lines=wrap(ref)
  if y-len(lines)*12<M+12:col=1;y=top
  for line in lines:put(ax,M+col*(CW+G),y,line);y-=12
  y-=8
 put(ax,W/2-3,27,'7',FontProperties(family='Liberation Serif',size=9));out.savefig(fig);plt.close(fig)

# Editable companion: page-by-page two-column tables preserve clear text and images.
ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def esc(s):return html.escape(s,quote=True)
def para(text,b=False,size=20,breakbefore=False):
 return '<w:p><w:pPr><w:spacing w:after="50" w:line="240" w:lineRule="auto"/>'+('<w:pageBreakBefore/>' if breakbefore else '')+'</w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="'+str(size)+'"/>'+('<w:b/>' if b else '')+'</w:rPr><w:t xml:space="preserve">'+esc(text)+'</w:t></w:r></w:p>'
rels=[];media={};body=''
for i,page in enumerate(d['pages']):
 if i:body+=para('',breakbefore=True,size=2)
 if i==0:body+=para(d['title'],True,32)+para(d['author'])+para(d['date'],size=18)
 body+=para(page['heading'],True,24)
 if 'figure' in page:
  imagepath=ROOT/'figures'/(page['figure']+'.png');im=Image.open(imagepath);cx=int(174/25.4*914400);cy=int(cx*im.height/im.width);rid='rId'+str(i)
  media[imagepath.name]=imagepath;rels.append((rid,imagepath.name))
  body+=f'<w:p><w:r><w:drawing><wp:inline><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{i}" name="Figure {i}"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{imagepath.name}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
  body+=para('Figure '+str(i)+'. '+page['caption'],size=17)
 body+='<w:tbl><w:tblPr><w:tblW w:w="9864" w:type="dxa"/><w:tblBorders>'+''.join('<w:'+s+' w:val="nil"/>' for s in ['top','left','bottom','right','insideH','insideV'])+'</w:tblBorders><w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid><w:gridCol w:w="4932"/><w:gridCol w:w="4932"/></w:tblGrid><w:tr>'
 for col in layouts[i]:
  body+='<w:tc><w:tcPr><w:tcW w:w="4932" w:type="dxa"/></w:tcPr>'
  for heading,text in col:body+=para(heading,True)+para(text)
  body+='</w:tc>'
 body+='</w:tr></w:tbl><w:p/>'
body+=para('References',True,24,True)
for ref in d['references']:body+=para(ref)
body+='<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1020" w:right="1020" w:bottom="1020" w:left="1020" w:header="400" w:footer="400"/></w:sectPr>'
document='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="'+ns+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>'+body+'</w:body></w:document>'
with zipfile.ZipFile(ROOT/'Feeding_Frenzy_Working_Draft.docx','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
 z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
 z.writestr('word/document.xml',document)
 z.writestr('word/_rels/document.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>' for rid,name in rels)+'</Relationships>')
 for name,path in media.items():z.write(path,'word/media/'+name)

# Preserve a compile-ready LaTeX source alongside the editable/print deliverables.
def tex(s):
 s=s.replace('’', chr(39)).replace('‘', chr(39)).replace('“', chr(96)*2).replace('”', chr(39)*2)
 for a,b in [ ('\\','\\textbackslash{}'),('%','\\%'),('&','\\&'),('_','\\_'),('#','\\#'),('Δ','\\ensuremath{\\Delta}'),('π','\\ensuremath{\\pi}'),('−','-'),('·','-'),('–','--'),('→','\\ensuremath{\\rightarrow}'),('≥','\\ensuremath{\\geq}'),('×','\\ensuremath{\\times}') ]:s=s.replace(a,b)
 return s
CITE_KEYS={1:'teske2021',2:'odonoghue2009',3:'lett2014',4:'thiebault2016',5:'couzin2002',6:'ropert2004',7:'mohapatra2025',8:'licht2026'}
def cite_tex(value):
 return re.sub(r'\[(\d)\]',lambda match: '\\citep{'+CITE_KEYS[int(match[1])]+'}',tex(value))

parts=[r'\documentclass[10pt,a4paper]{article}',r'\usepackage[margin=18mm,columnsep=6mm]{geometry}',r'\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{mathptmx,microtype,graphicx,caption,amsmath}',r'\usepackage[numbers,sort&compress]{natbib}\usepackage[hidelinks]{hyperref}\usepackage{xurl}\setlength{\bibsep}{4pt}',r'\captionsetup{font=small,labelfont=bf,skip=5pt}\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}',r'\begin{document}']
for i,page in enumerate(d['pages']):
 if i:parts.append(r'\clearpage')
 if i==0:parts.append(r'\begin{center}{\LARGE\bfseries '+tex(d['title'])+r'\par}\vspace{6pt}'+tex(d['author'])+r'\par{\small '+tex(d['date'])+r'}\end{center}')
 parts.append(r'{\large\bfseries '+tex(page['heading'])+r'\par}\vspace{7pt}')
 if 'figure' in page:parts.append(r'\begin{minipage}{\textwidth}\centering\includegraphics[width=\linewidth]{figures/'+page['figure']+r'.pdf}\captionof{figure}{'+tex(page['caption'])+r'}\end{minipage}\par\vspace{7pt}')
 for col_number,col in enumerate(layouts[i]):
  if col_number:parts.append(r'\hfill')
  parts.append(r'\begin{minipage}[t]{'+str(CW)+r'pt}\vspace{0pt}')
  for h,t in col:parts.append(r'\textbf{'+tex(h)+r'}\par '+cite_tex(t)+r'\par\smallskip')
  parts.append(r'\end{minipage}')
parts += [r'\twocolumn\bibliographystyle{unsrtnat}\bibliography{references}',r'\end{document}']
(ROOT/'main.tex').write_text('\n'.join(parts)+'\n')
for name in ['references.bib']:(ROOT/name).write_bytes((ROOT/'original_downloads'/name).read_bytes())
(ROOT/'build_validation.json').write_text(json.dumps(dict(at=datetime.now(ZoneInfo('Australia/Perth')).isoformat(),body_pages=6,reference_pages=1,numbered_figures=4,body_font_points=10,margins_mm=18,columns=2,renderer='matplotlib vector PDF; editable DOCX companion',latex_compiler_network_unavailable=True,replication_captures_alone=87,replication_captures_with_gannets=101,word_count=sum(len(t.split()) for p in d['pages'] for h,t in p['paragraphs'])),indent=2))
print(pdf)
