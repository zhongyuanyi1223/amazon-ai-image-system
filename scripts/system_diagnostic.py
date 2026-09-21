"""Project-local configuration checks; no claims about live model or image access."""
import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
import yaml
from core import ROOT, read, policy, schema_validate, require
from jsonschema import Draft202012Validator

def inspect():
    cfg=tomllib.loads((ROOT/'.codex/config.toml').read_text(encoding='utf-8'))
    pol=policy(); skills=[]; implicit=[]; agents=[]
    for p in sorted((ROOT/'.agents/skills').glob('*/SKILL.md')):
        text=p.read_text(encoding='utf-8'); front=yaml.safe_load(text.split('---',2)[1])
        require(front['name']==p.parent.name and bool(front['description']),'SKILL',str(p))
        meta=yaml.safe_load((p.parent/'agents/openai.yaml').read_text(encoding='utf-8'))
        if meta['policy']['allow_implicit_invocation']: implicit.append(front['name'])
        require((p.parent/'references/contract.md').is_file(),'SKILL','Missing skill contract')
        skills.append(front['name'])
    require(len(skills)==9 and implicit==['amazon-image-director'],'ENTRY','Only Director may be implicitly invoked')
    for p in sorted((ROOT/'.codex/agents').glob('*.toml')):
        agent=tomllib.loads(p.read_text(encoding='utf-8'))
        require(set(agent)>={'name','description','developer_instructions'},'AGENT',str(p))
        require(agent['model']==pol['reasoning_model'] and agent['model_reasoning_effort']==pol['reasoning_effort'],'MODEL','Agent policy drift')
        agents.append(agent['name'])
    require(len(agents)==5 and len(set(agents))==5,'AGENT','Expected five distinct agents')
    require(cfg['model']==pol['reasoning_model'] and cfg['model_reasoning_effort']==pol['reasoning_effort'],'MODEL','Project model policy drift')
    require(cfg['agents']['default_subagent_model']==pol['reasoning_model'] and cfg['agents']['default_subagent_reasoning_effort']==pol['reasoning_effort'],'MODEL','Subagent default policy drift')
    for p in (ROOT/'schemas').glob('*.json'): Draft202012Validator.check_schema(read(p))
    for name,template in [('product','product-card'),('image-job','image-job'),('image-plan','image-plan'),('qc-result','qc-report')]: schema_validate(read(ROOT/f'templates/{template}.template.json'),name)
    for filename in ['AGENTS.md','README.md','config/workflow-policy.md','config/question-policy.md','scripts/validate_job.py','scripts/validate_qc.py','scripts/validate_schema.py','scripts/workflow.py']:
        require((ROOT/filename).is_file(),'FILE',f'Missing {filename}')
    fixture_count=len([p for p in (ROOT/'tests').glob('*.json') if p.name!='entry-routing.json'])
    require(fixture_count>=10,'TESTS','At least ten core fixtures required')
    cases=read(ROOT/'tests/entry-routing.json')
    require(len(cases)>=5 and all(c['expected_skill']=='amazon-image-director' for c in cases),'ENTRY','Missing routing cases')
    return {'status':'PASS','project_root':str(ROOT),'AGENTS.md':'PRESENT','skills':skills,'agents':agents,'entry':'amazon-image-director','implicit_skills':implicit,'reasoning_model':cfg['model'],'reasoning_effort':cfg['model_reasoning_effort'],'requested_image_model':pol['image_generation']['model'],'knowledge_version':'2026-09-20.1','schemas':'PASS','validators':'PRESENT; use --run-tests to execute','core_fixture_count':fixture_count,'routing_fixture_count':len(cases),'live_routing':'NOT_RUN','live_image_generation':'NOT_RUN','live_visual_qc':'NOT_RUN','actual_native_model':'UNKNOWN','tests':'NOT_RUN'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--run-tests',action='store_true'); p.add_argument('--output',type=Path); a=p.parse_args()
    try:
        report=inspect()
        if a.run_tests:
            result=subprocess.run([sys.executable,str(ROOT/'scripts/run_tests.py')],capture_output=True,text=True,encoding='utf-8')
            report['tests']='PASS' if result.returncode==0 else 'FAIL'
            match=re.search(r'Ran (\d+) tests',result.stderr); report['test_methods']=int(match[1]) if match else None
            if result.returncode: report['status']='FAIL'; report['test_log']=result.stdout+result.stderr
        text=json.dumps(report,ensure_ascii=False,indent=2)
        if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text+'\n',encoding='utf-8')
        print(text)
        return 0 if report['status']=='PASS' else 1
    except Exception as e:
        print(json.dumps({'status':'FAIL','message':str(e)},ensure_ascii=False)); return 1
if __name__=='__main__': sys.exit(main())
