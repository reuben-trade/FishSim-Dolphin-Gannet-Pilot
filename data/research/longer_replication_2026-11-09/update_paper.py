"""Apply the reviewed eight-school results template after all evidence validates.

Builds a private candidate first. Canonical local files change only after layout,
figure count, source receipts and the approved template hashes pass. No external
publication or native simulation is performed.
"""
from __future__ import annotations
import csv
import ast
from datetime import datetime
import hashlib
import json
import importlib.util
import inspect
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from zoneinfo import ZoneInfo
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
PAPER=HERE.parent/'thesis_working_draft_2026-11-08'
ANALYSIS=HERE/'results/analysis_final'
RUN=HERE/'results/full_72T_v1'


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def stamp():return datetime.now(ZoneInfo('Australia/Perth')).isoformat()
def signed(value):return f'{value:+.2f}'
def interval_text(values):return f'{values[0]:+.2f} to {values[1]:+.2f}'
def table(path):
    with Path(path).open(newline='') as handle:return list(csv.DictReader(handle))


def publication_figure(pairs,statistics,output):
    # Full reset keeps these pixels independent of whichever other paper figure
    # was generated earlier, while preserving its caller's plotting style.
    with matplotlib.rc_context(matplotlib.rcParamsDefault):
        return _publication_figure(pairs,statistics,output)


def _publication_figure(pairs,statistics,output):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5,'axes.spines.top':False,
        'axes.spines.right':False,'pdf.fonttype':42,'savefig.facecolor':'white'})
    fig,axes=plt.subplots(1,2,figsize=(7.05,2.45),sharex=True)
    for ax,species,color,title in zip(axes,('D','G'),('#087F8C','#D98525'),('Dolphin partner effect','Gannet partner effect')):
        ax.axhline(0,color='#73818B',linewidth=.7)
        points={}
        for index,horizon in enumerate((36.,72.)):
            group=sorted((r for r in pairs if float(r['horizon_T'])==horizon),key=lambda r:int(r['school_seed']))
            assert len(group)==8
            y=np.asarray([float(r[species+'_difference']) for r in group]);x=index+np.linspace(-.16,.16,8)
            ax.scatter(x,y,s=21,color=color,alpha=.8,zorder=3,label='School difference' if index==0 else None)
            mean=float(y.mean());ax.scatter([index],[mean],marker='D',s=34,color='#263746',zorder=5,
                label='Mean' if index==0 else None)
            points[str(int(horizon))]=dict(schools=[int(r['school_seed']) for r in group],differences=y.tolist(),mean=mean)
            if horizon==36.:
                low,high=statistics[species]['interval']
                ax.vlines(index,low,high,color='#263746',lw=1.4,zorder=4)
                ax.hlines([low,high],index-.07,index+.07,color='#263746',lw=1.4,zorder=4)
                points['36']['marginal_97_5_percent_interval']=[low,high]
        ax.set(xticks=[0,1],xticklabels=['36T primary','72T secondary'],xlim=(-.42,1.42),
            title=title,ylabel='Mixed − alone captures')
        ax.grid(axis='y',alpha=.18)
        if species=='D':ax.legend(frameon=False,fontsize=7,loc='best')
    fig.tight_layout(pad=.8)
    for ext in ('png','pdf'):fig.savefig(output/('fig3_replication.'+ext),dpi=230,bbox_inches='tight',pad_inches=.035)
    plt.close(fig)
    return dict(D=axes_data(pairs,'D'),G=axes_data(pairs,'G'),primary_statistics=statistics)


def axes_data(pairs,species):
    return {str(int(h)):[dict(school=int(r['school_seed']),difference=float(r[species+'_difference']))
        for r in sorted(pairs,key=lambda r:int(r['school_seed'])) if float(r['horizon_T'])==h] for h in (36.,72.)}


def interval_verdict(statistics):
    labels={}
    for species in ('D','G'):
        low,high=statistics[species]['interval']
        labels[species]='lay above zero' if low>0 else 'lay below zero' if high<0 else 'included zero'
    statement=f'The dolphin primary interval {labels["D"]}; the gannet interval {labels["G"]}. '
    if all(statistics[s]['interval'][0]>0 for s in ('D','G')):
        statement+='Both intervals are consistent with positive average same-policy partner effects under this fixed model. '
    else:
        statement+='The two primary intervals do not jointly support positive average partner effects for both species. '
    return statement+'This interpretation remains limited by eight schools, percentile-bootstrap uncertainty and uncalibrated model assumptions.'


def updated_plot_builder(original,caption):
    """Keep the canonical plotter and portable notebook reproduction aligned."""
    node=next(n for n in ast.parse(original).body if getattr(n,'name',None)=='replication_figure')
    helpers='\n\n'.join(inspect.getsource(f) for f in (publication_figure,_publication_figure,axes_data))
    function='''def replication_figure():
    analysis=LONGER/'results/analysis_final'
    audit=read(analysis/'analysis_audit.json')
    assert audit['status']=='passed' and audit['sealed_horizon_records']==48 and not audit['pending']
    pairs=table(analysis/'paired_horizons.csv');statistics=read(analysis/'primary_statistics.json')
    plan=read(LONGER/'analysis_plan.json')
    assert statistics['status']=='complete' and statistics['independent_schools']==8 and len(pairs)==16
    inputs=[analysis/'paired_horizons.csv',analysis/'primary_statistics.json',analysis/'analysis_audit.json',LONGER/'analysis_plan.json',Path(__file__)]
    by={(int(r['school_seed']),float(r['horizon_T'])):r for r in pairs}
    for school in range(39064501,39064509):
        for horizon in (36.,72.):
            states={}
            for presence in ('D','G','DG'):
                directory=LONGER/'results/full_72T_v1/cases'/f's{school}_exposed_{presence}_c61001'
                seal_path=directory/f'checkpoint_{horizon:g}T.seal.json';seal=read(seal_path)
                assert seal['status']=='complete'
                for name,digest in seal['files'].items():assert sha(directory/name)==digest
                data_path=directory/f'checkpoint_{horizon:g}T.json'
                states[presence]=read(data_path);inputs.extend([seal_path,data_path])
            row=by[(school,horizon)]
            for field,presence,species in (('D_alone','D','D'),('D_with_gannets','DG','D'),('G_alone','G','G'),('G_with_dolphins','DG','G')):
                assert int(row[field])==states[presence]['species'][species]['captures']
            assert int(row['D_difference'])==int(row['D_with_gannets'])-int(row['D_alone'])
            assert int(row['G_difference'])==int(row['G_with_dolphins'])-int(row['G_alone'])
    vectors=np.asarray([[float(by[(s,36.)]['D_difference']),float(by[(s,36.)]['G_difference'])] for s in range(39064501,39064509)])
    generator=np.random.default_rng(plan['bootstrap']['seed'])
    draws=generator.integers(0,8,size=(plan['bootstrap']['draws'],8))
    intervals=np.quantile(vectors[draws].mean(axis=1),plan['bootstrap']['quantiles'],axis=0)
    for index,species in enumerate(('D','G')):
        assert statistics[species]['mean_difference']==float(vectors[:,index].mean())
        assert np.array_equal(np.asarray(statistics[species]['interval']),intervals[:,index])
    OUT.mkdir(parents=True,exist_ok=True)
    plotted=publication_figure(pairs,statistics,OUT)
    caption=CAPTION_LITERAL
    receipt_path=OUT/'figure_receipts.json';receipts=read(receipt_path) if receipt_path.exists() else {}
    receipts['fig3_replication']=dict(caption=caption,sources=[source(p) for p in inputs],plotted_data=plotted,
        created_at=datetime.now(ZoneInfo('Australia/Perth')).isoformat(),native_steps=0,
        outputs={ext:source(OUT/('fig3_replication.'+ext)) for ext in ('pdf','png')},
        uncertainty_intervals='97.5% marginal school-vector bootstrap at36T only;72T descriptive')
    receipt_path.write_text(json.dumps(receipts,indent=2,allow_nan=False)+'\\n')
    (OUT/'captions.txt').write_text('\\n\\n'.join(key+': '+receipts[key]['caption'] for key in sorted(receipts))+'\\n')
    print('fig3_replication: eight independent schools,36Tprimary/72Tsecondary',flush=True)
    return True
'''.replace('CAPTION_LITERAL',repr(caption))
    lines=original.splitlines(True)
    result=''.join(lines[:node.lineno-1])+helpers+'\n\n'+function+'\n'+''.join(lines[node.end_lineno:])
    anchor="REPLICATION=RESEARCH/'exposed_replication_2026-11-08'"
    assert anchor in result
    return result.replace(anchor,anchor+"\nLONGER=RESEARCH/'longer_replication_2026-11-09'",1)


def update_content(original,pairs,statistics):
    value=json.loads(json.dumps(original));primary=[r for r in pairs if float(r['horizon_T'])==36.]
    secondary=[r for r in pairs if float(r['horizon_T'])==72.]
    assert len(primary)==len(secondary)==8
    total=lambda rows,key:sum(int(r[key]) for r in rows)
    da,dm,ga,gm=(total(primary,k) for k in ('D_alone','D_with_gannets','G_alone','G_with_dolphins'))
    da72,dm72,ga72,gm72=(total(secondary,k) for k in ('D_alone','D_with_gannets','G_alone','G_with_dolphins'))
    joint=statistics['joint_positive'];joint72=sum(r['joint_positive']=='True' for r in secondary)
    depleted=sum(read(path)['native_absorbing_termination'] for path in (RUN/'cases').glob('*/summary.json'))
    dmean,gmean=statistics['D']['mean_difference'],statistics['G']['mean_difference']
    summary=(f'Across eight independent schools at the prespecified36T primary horizon, dolphin captures totalled {da} alone and {dm} with gannets; '
        f'gannet captures totalled {ga} alone and {gm} with dolphins. Equal-school mean differences were {signed(dmean)} dolphin captures '
        f'and {signed(gmean)} gannet captures. The97.5% marginal percentile intervals were {interval_text(statistics["D"]["interval"])} '
        f'and {interval_text(statistics["G"]["interval"])}, respectively. Both differences were strictly positive in {joint} of8 schools.')
    value['replication_result']=summary
    value['replication_verdict']=interval_verdict(statistics)
    value['replication_counts']={'D_alone':da,'D_mixed':dm,'G_alone':ga,'G_mixed':gm,'independent_schools':8}
    value['date']='Working draft · 9 November 2026 · eight-school extension'
    def replace(page,heading,text):
        entries=value['pages'][page]['paragraphs']
        index=next(i for i,(h,_) in enumerate(entries) if h==heading);entries[index]=[heading,text]
    replace(0,'Abstract',
        'Dolphins and Cape gannets feed on the same fish schools, but association alone does not establish mutual benefit. '
        'We compare species-specific feeding returns in a three-dimensional agent-based model. Dolphins repeat local herding, '
        'a feasible strike and recovery. An exploratory policy comparison selected exposed-prey targeting for a same-policy partner test. '
        f'A prespecified extension used eight independent new schools, each with dolphin-only, gannet-only and mixed72T encounters. '
        f'At the36T primary horizon, mean mixed-minus-alone changes were {signed(dmean)} dolphin and {signed(gmean)} gannet captures; '
        f'both species gained in {joint} of8 schools. Secondary72T outcomes describe persistence within the same trajectories. '
        'Earlier depth experiments were transient initial-state contrasts. All results remain conditional on uncalibrated perception, '
        'herding and contact-success assumptions; controlled timing and numerical convergence remain separate tests.')
    replace(2,'Outcome and duration',
        'For species s, feeding return is Y_s=C_s/(N_s T), where C_s counts uniquely removed fish, N_s is predator abundance '
        'and T is the prespecified elapsed horizon. Effects compare mixed with same-policy alone conditions for each species. '
        'Development encounters lasted36T. The new extension lasts72T with36T fixed in advance as the primary horizon;72T and36–72T increments are secondary. '
        'All travel, herding, missed attacks, handling and recovery count toward elapsed time. Predator-free20T preparation is excluded. '
        'Complete prey depletion fixes later capture counts, while native stepping and effort accounting end at the actual depletion time.')
    value['pages'][3]['heading']='4 Prespecified replication on eight new schools'
    value['pages'][3]['caption']=(
        'Eight-school replication of the unchanged exposed-prey rule. Each point is one school’s mixed-minus-alone capture difference. '
        'Diamonds show equal-school means. Bars at36T are97.5% marginal percentile bootstrap intervals for the two primary species '
        '(approximate95% familywise coverage, with small-sample limitations). The72T outcomes are descriptive extensions of the same trajectories. '
        'No historical development or two-school follow-up data enter these estimates.')
    value['pages'][3]['paragraphs']=[
        ['Frozen design','Eight new starting schools were declared before feeding outcomes. Each retained the original sampler,160 fish, '
         'predator-free20T checkpoint, physical model and exposed-prey controller. The original36T stability screen and an additional36T '
         'predator-free route check passed for every fixed candidate; none was replaced. One stochastic setting per school produced matched D, G and DG '
         'encounters, with12 dolphins and/or3 gannets. Private species capture and target-choice streams, contact ties and physical starts matched within triplets.'],
        ['Primary outcome',summary],
        ['Independent units and uncertainty','The independent unit is the starting school, giving n=8 paired vectors. Means weight schools equally. '
         'A fixed-seed10,000-draw bootstrap resamples entire paired dolphin–gannet school vectors. The two97.5% marginal intervals target approximate95% '
         'familywise coverage, but percentile interval coverage and tails can be unstable at this sample size. Development comparisons selected the policy; '
         'the earlier fresh two-school pilot motivated this extension. Neither is pooled into this estimate.'],
        ['Longer encounter','At72T, dolphin captures totalled '+str(da72)+' alone and '+str(dm72)+' with birds; gannet captures totalled '+str(ga72)+
         ' alone and '+str(gm72)+' with dolphins. Jointly positive school differences numbered '+str(joint72)+' of8. '+str(depleted)+
         ' of24 encounters reached complete prey depletion. These are secondary outcomes from the same trajectories, not another independent sample. '
         'The36–72T increments and observed effort are reported separately in the companion tables.'],
        ['Verification','Each36T checkpoint has its own sealed ordered event prefix, physical fish state and random-stream receipts. '
         'The72T continuation was checked against that exact prefix and the saved36T trajectory frame. All24 cases passed unique-removal, '
         'eligible-contact, recovery, cycle-gating and random-stream replay checks. Actual native duration is distinguished from nominal horizons after depletion. '
         'These implementation checks do not establish biological calibration or timestep convergence.']]
    value['pages'][4]['heading']='5 Earlier gannet controls, depth and timing'
    value['pages'][4]['caption']='Earlier two-school controls and initial-depth pilot, kept separate from the eight-school replication. '+value['pages'][4]['caption']
    replace(4,'Matching gannet controls',
        'Before the eight-school extension, eight additional36T gannet-only encounters were completed. Four unshifted controls match the earlier '
        'two-school follow-up and its two random settings. Their birds retain the same capabilities, initial states and private capture and target-choice '
        'streams as the mixed counterparts. Four other encounters translate each school to initial mean depths8 and11 using setting61001. '
        'Translation preserves geometry without clipping; the preferred fish depth remains5 with deadband3–7. These earlier outcomes do not enter Figure3.')
    replace(5,'Interpretation',
        'The development comparison showed that the partner effect depends on target selection and starting school: exposed targeting had a positive '
        'pooled response while nearest targeting produced more total food. The prespecified eight-school extension estimates the same-policy partner effect '
        f'with mean36T changes of {signed(dmean)} dolphin and {signed(gmean)} gannet captures and joint positive differences in {joint} of8 schools. '
        +interval_verdict(statistics)+' Neither pooled total nor one favourable trajectory establishes uniform reciprocal benefit.')
    replace(5,'Conclusion',
        'The study supplies a reproducible matched test of specified herd–strike rules, including both species’ alone controls and a longer within-encounter '
        'follow-up across eight new schools. '+interval_verdict(statistics)+' These outcomes do not establish deliberate '
        'coordination, energetic profitability or evolutionary stability. Timing interventions, numerical sensitivity and calibration of herding, perception and '
        'contact success remain necessary before a general ecological conclusion.')
    replace(5,'Reproducibility and draft status',
        'The timestep is0.00125T:36T requires28,800 steps and72T at most57,600. Source and checkpoint hashes, random states, ordered contact logs, '
        'trajectories and sealed horizon summaries are retained. After complete depletion, later feeding counts are exactly fixed; later effort is not invented. '
        'The current published notebook verifies24 earlier development, replication and gannet-only/depth cases; its18 default cells passed, including relocation. '
        'The new24-case eight-school extension is not included in that snapshot: an aligned refreshed notebook remains pending its own validation and publication. '
        'Optional model execution has documented platform restrictions. Code and evidence: https://github.com/reuben-trade/FishSim-Dolphin-Gannet-Pilot. '
        'Calibration, convergence and timing remain open.')
    for page in value['pages']:
        page['caption']=re.sub(r'(?<=[a-z])(?=\d)',' ',page['caption']) if 'caption' in page else page.get('caption','')
        page['paragraphs']=[[heading,re.sub(r'(?<=[a-z])(?=\d)',' ',text)] for heading,text in page['paragraphs']]
    return value


def main():
    approval=read(HERE/'PAPER_TEMPLATE_APPROVED.json');assert approval.get('approved') is True
    assert approval['update_script_sha256']==sha(Path(__file__))
    for relative,digest in approval['canonical_template_sha256'].items():assert sha(PAPER/relative)==digest,relative
    audit=read(ANALYSIS/'analysis_audit.json');statistics=read(ANALYSIS/'primary_statistics.json')
    assert audit['status']=='passed' and audit['sealed_horizon_records']==48 and not audit['pending']
    assert len(audit['physical_prefix_continuation'])==24
    physical=read(RUN/'physical_review.json');assert physical['status']=='passed' and len(physical['cases'])==24
    assert statistics['status']=='complete' and statistics['independent_schools']==8
    pairs=table(ANALYSIS/'paired_horizons.csv');assert len(pairs)==16
    candidate=HERE/'publication_candidate';candidate.mkdir(exist_ok=False)
    shutil.copytree(PAPER/'figures',candidate/'figures')
    shutil.copytree(PAPER/'original_downloads',candidate/'original_downloads')
    shutil.copy2(PAPER/'build_latex_pdf.py',candidate/'build_latex_pdf.py')
    shutil.copy2(PAPER/'references.bib',candidate/'references.bib')
    content=update_content(read(PAPER/'paper_content.json'),pairs,statistics)
    write(candidate/'paper_content.json',content)
    plotted=publication_figure(pairs,statistics,candidate/'figures')
    builder=updated_plot_builder((PAPER/'build_paper_figures.py').read_text(),content['pages'][3]['caption'])
    (candidate/'build_paper_figures.py').write_text(builder)
    spec=importlib.util.spec_from_file_location('_new_paper_plot_reproduction',candidate/'build_paper_figures.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.LONGER=HERE;module.OUT=candidate/'reproduced_figure3';module.replication_figure()
    import matplotlib.image as mpimg
    assert np.array_equal(mpimg.imread(candidate/'figures/fig3_replication.png'),
        mpimg.imread(candidate/'reproduced_figure3/fig3_replication.png')),'Canonical Figure3 source does not reproduce candidate pixels'
    receipt=read(candidate/'figures/figure_receipts.json')
    receipt['fig3_replication']=dict(caption=content['pages'][3]['caption'],plotted_data=plotted,
        sources=[dict(path=str(ANALYSIS/name),sha256=sha(ANALYSIS/name)) for name in ('paired_horizons.csv','primary_statistics.json','analysis_audit.json')],
        horizon_seals=[dict(path=str(path),sha256=sha(path)) for path in sorted((RUN/'cases').glob('*/checkpoint_*T.seal.json'))],
        plotting_source=dict(path=str(PAPER/'build_paper_figures.py'),sha256=sha(candidate/'build_paper_figures.py')),
        native_steps=0,created_at=stamp(),outputs={ext:dict(path=str(candidate/'figures'/('fig3_replication.'+ext)),
            sha256=sha(candidate/'figures'/('fig3_replication.'+ext))) for ext in ('pdf','png')})
    write(candidate/'figures/figure_receipts.json',receipt)
    (candidate/'figures/captions.txt').write_text('\n\n'.join(key+': '+entry['caption'] for key,entry in receipt.items())+'\n')
    renderer=(PAPER/'render_working_draft.py').read_text()
    renderer,count_summary=re.subn(r'^summary=.*$',"summary=d['replication_result']",renderer,count=1,flags=re.M)
    renderer,count_verdict=re.subn(r'^verdict=.*$',"verdict=d['replication_verdict']",renderer,count=1,flags=re.M)
    assert count_summary==count_verdict==1
    old='replication_captures_alone=87,replication_captures_with_gannets=101'
    assert old in renderer
    renderer=renderer.replace(old,"replication_captures_alone=d['replication_counts']['D_alone'],replication_captures_with_gannets=d['replication_counts']['D_mixed']")
    (candidate/'render_working_draft.py').write_text(renderer)
    with (candidate/'render.log').open('w') as log:
        subprocess.run([sys.executable,str(candidate/'render_working_draft.py')],cwd=candidate,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run([sys.executable,str(candidate/'build_latex_pdf.py')],cwd=candidate,stdout=log,stderr=subprocess.STDOUT,check=True)
    validation=read(candidate/'build_validation.json')
    assert validation['body_pages']==6 and validation['reference_pages']==1 and validation['numbered_figures']==4
    assert validation['compiled_pages']==7 and validation['verified_citations']==8
    assert validation['numbered_figures_verified']==4 and validation['missing_glyphs'] is False and validation['overflow'] is False
    assert validation['current_pdf_sha256']==sha(candidate/'Feeding_Frenzy_Working_Draft.pdf')
    assert len(content['pages'])==6 and sum('figure' in page for page in content['pages'])==4
    assert (candidate/'main.tex').read_text().count('\\captionof{figure}')==4
    pdfinfo=shutil.which('pdfinfo')
    if pdfinfo:
        info=subprocess.run([pdfinfo,str(candidate/'Feeding_Frenzy_Working_Draft.pdf')],capture_output=True,text=True,check=True).stdout
        assert re.search(r'^Pages:\s+7\s*$',info,re.M)
    with zipfile.ZipFile(candidate/'Feeding_Frenzy_Working_Draft.docx') as archive:
        assert archive.testzip() is None and len([n for n in archive.namelist() if n.startswith('word/media/')])==4
    # Preserve the complete pre-update local deliverables before promoting.
    archive=HERE/'paper_before_eight_school_update';archive.mkdir(exist_ok=False)
    promote=['paper_content.json','paper_content_resolved.json','render_working_draft.py','build_latex_pdf.py','build_paper_figures.py','Feeding_Frenzy_Working_Draft.pdf',
        'Feeding_Frenzy_Working_Draft.docx','main.tex','main.pdf','main.bbl','main.aux','main.log','references.bib','latex_build_output.log','build_validation.json',
        'figures/fig3_replication.png','figures/fig3_replication.pdf','figures/figure_receipts.json','figures/captions.txt']
    for name in promote:
        source=PAPER/name
        if source.exists():(archive/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,archive/name)
    for relative,digest in approval['canonical_template_sha256'].items():assert sha(PAPER/relative)==digest,'Template changed during candidate build'
    for name in promote:shutil.copy2(candidate/name,PAPER/name)
    write(HERE/'paper_update_validation.json',dict(status='passed',at=stamp(),body_pages=6,references=1,numbered_figures=4,
        primary_independent_schools=8,primary_T=36,secondary_T=72,source_horizon_records=48,
        compiled_latex=True,verified_citations=8,canonical_figure3_reproduction='pixel-identical',
        publication='local only; external publication pending separate validated workflow',
        source_analysis_sha256=sha(ANALYSIS/'analysis_audit.json'),files={name:sha(PAPER/name) for name in promote},
        candidate=str(candidate),prior_archive=str(archive),native_steps=0))
    print(json.dumps(dict(status='passed',local_pdf=str(PAPER/'Feeding_Frenzy_Working_Draft.pdf'),native_steps=0)))


if __name__=='__main__':main()
