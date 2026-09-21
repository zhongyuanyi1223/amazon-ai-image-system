"""Behavioral tests use synthetic local fixtures, never a live image service."""
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import *
from workflow import create, add_prompt, record_image, apply_report, save, locked

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aR3sAAAAASUVORK5CYII=')

def fact(value):
    return {'value':value,'status':'CONFIRMED','sources':['operator: test fixture'],'note':''}

def ready_job(folder, count=1):
    job=create(folder,'TEST-SKU')
    (folder/'inputs/reference.png').write_bytes(PNG)
    (folder/'inputs/brief.txt').write_text('Synthetic test: one white steel hook, no accessories or load claim.',encoding='utf-8')
    reference={'path':'inputs/reference.png','sha256':file_hash(folder/'inputs/reference.png')}
    values={'product_identity':'test hook','structure':'one curved hook','material':'steel','color':'white','quantity':1,'dimensions':'10 cm','accessories':[],'supported_claims':[],'immutable_features':['one hook','one mounting hole'],'forbidden_changes':['no additional hooks'],'reference_images':[reference]}
    job['product']={k:fact(v) for k,v in values.items()}
    job['requirements']={'platform':fact('Amazon'),'marketplace':fact('US'),'image_type':fact('main' if count==1 else 'image_set'),'material_affects_visual':True,'source_documents':[{'kind':'equivalent_product_brief','path':'inputs/brief.txt','sha256':file_hash(folder/'inputs/brief.txt')}]}
    job['plan']['images'][0]['evidence']=['inputs/brief.txt','inputs/reference.png']
    for index in range(1,count):
        slot=copy.deepcopy(job['plan']['images'][0]); slot.update(image_id=f'{index+1:02d}-detail',type='detail'); job['plan']['images'].append(slot)
    job['generation']['capability']={'native_available':True,'selectable_model':True,'available_models':['gpt-image-2','test-alternate-image-model'],'evidence':'synthetic test capability; not an account availability assertion'}
    for state in ['COLLECTING','ANALYZING','VALIDATING','WAITING_FOR_CONFIRMATION']: transition(job,state,'test')
    return job

def prompt_ready(job,folder):
    confirm(job,folder,'确认生成','fixture-operator')
    transition(job,'PLANNING','test')
    source=folder/'inputs/prompt.txt'; source.write_text('Synthetic test prompt preserving locked facts.',encoding='utf-8')
    for image in job['plan']['images']: add_prompt(job,folder,image['image_id'],source)
    transition(job,'PROMPT_READY','test')

def generated(job,folder):
    begin(job,folder)
    for image_id in list(job['active_images']):
        record_image(job,folder,image_id,folder/'inputs/reference.png',job['generation']['model'])

def report(job,image_id='01-main',status='PASS'):
    template=read(ROOT/'templates/qc-report.template.json')
    template.update(job_id=job['job_id'],image_id=image_id,asset_sha256=job['artifacts'][image_id]['sha256'],confirmation_digest=binding(job),status=status,reviewer='fixture-only',reviewed_at=now())
    template['checks']={k:'PASS' for k in template['checks']}; template['issues']=[]
    if status=='FAIL':
        template['checks']['product_consistency']='FAIL'
        template['issues']=[{'severity':'critical','type':'quantity','description':'Synthetic wrong hook count.','repair_instruction':'Restore one hook and preserve other details.'}]
    return template

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.folder=Path(self.temp.name)/'job'; self.job=ready_job(self.folder)
    def tearDown(self): self.temp.cleanup()
    def blocked(self,code,fn,*args,**kwargs):
        with self.assertRaises(Blocked) as caught: fn(*args,**kwargs)
        self.assertEqual(caught.exception.code,code)

    def test_core_scenarios(self):
        fixtures=sorted((ROOT/'tests').glob('*.json'))
        fixtures=[f for f in fixtures if f.name!='entry-routing.json']
        self.assertEqual(len(fixtures),10)
        for fixture in fixtures:
            case=read(fixture)
            with self.subTest(case=fixture.stem), tempfile.TemporaryDirectory() as td:
                folder=Path(td)/'job'; job=ready_job(folder); action=case['action']
                if action=='missing_material':
                    job['product']['material'].update(value=None,status='MISSING'); self.blocked(case['code'],validate_ready,job,folder)
                elif action.startswith('conflict_'):
                    job['product'][action.split('_')[1]]['status']='CONFLICT'; self.blocked(case['code'],validate_ready,job,folder)
                elif action=='missing_listing':
                    job['requirements']['source_documents']=[]; self.blocked(case['code'],validate_ready,job,folder)
                elif action=='unconfirmed': self.blocked(case['code'],validate_generation,job,folder)
                elif action=='confirmed':
                    prompt_ready(job,folder); self.assertEqual(validate_generation(job,folder),case['expected'])
                elif action=='locked_change':
                    prompt_ready(job,folder); job['product']['color']['value']='gray'; self.blocked(case['code'],validate_generation,job,folder)
                    invalidate(job,'operator_change'); self.assertFalse(job['generation']['confirmed'])
                elif action in {'qc_failure','qc_pass'}:
                    prompt_ready(job,folder); generated(job,folder); apply_report(job,folder,report(job,status='FAIL' if action=='qc_failure' else 'PASS')); self.assertEqual(job['state'],case['expected'])
                elif action=='model_switch':
                    before=(ROOT/'config/model-policy.md').read_bytes(); prompt_ready(job,folder)
                    switch_model(job,'test-alternate-image-model','确认'); self.assertEqual(job['generation']['scope'],'current_job'); self.assertFalse(job['generation']['confirmed']); self.assertEqual(before,(ROOT/'config/model-policy.md').read_bytes())
                else: self.fail('Unknown fixture action')

    def test_inferred_p0_blocked(self):
        self.job['product']['color']['status']='INFERRED'; self.blocked('P0',validate_ready,self.job,self.folder)
    def test_empty_identity_blocked(self):
        self.job['product']['product_identity']['value']=' '; self.blocked('P0',validate_ready,self.job,self.folder)
    def test_boolean_quantity_blocked(self):
        self.job['product']['quantity']['value']=True; self.blocked('SCHEMA',validate_ready,self.job,self.folder)
    def test_nonvisual_missing_material_allowed(self):
        self.job['requirements']['material_affects_visual']=False; self.job['product']['material'].update(value=None,status='MISSING'); validate_ready(self.job,self.folder)
    def test_inferred_dimension_blocks_size_slot(self):
        self.job['requirements']['image_type']=fact('secondary'); self.job['plan']['images'][0]['type']='size'; self.job['product']['dimensions']['status']='INFERRED'; self.blocked('P0',validate_ready,self.job,self.folder)
    def test_state_skip_blocked(self): self.blocked('STATE',transition,self.job,'FINAL','illegal')
    def test_history_tamper_blocked(self):
        self.job['state']='FINAL'; self.blocked('HISTORY',validate_history,self.job)
    def test_unavailable_tool_blocked(self):
        self.job['generation']['capability']['native_available']=False; self.blocked('CAPABILITY',validate_ready,self.job,self.folder)
    def test_native_unverified_requires_disclosure(self):
        self.job['generation']['capability']['selectable_model']=False
        self.blocked('MODEL_DISCLOSURE',confirm,self.job,self.folder,'确认','operator')
        confirm(self.job,self.folder,'确认','operator',True); validate_confirmation(self.job)
    def test_unknown_model_switch_blocked(self): self.blocked('MODEL_UNAVAILABLE',switch_model,self.job,'unavailable','确认')
    def test_model_switch_without_confirmation_blocked(self): self.blocked('UNCONFIRMED',switch_model,self.job,'test-alternate-image-model','maybe')
    def test_plan_change_invalidates_confirmation(self):
        prompt_ready(self.job,self.folder); self.job['plan']['images'][0]['scene']='different'; self.blocked('STALE_CONFIRMATION',validate_generation,self.job,self.folder)
    def test_capability_change_invalidates_confirmation(self):
        prompt_ready(self.job,self.folder); self.job['generation']['capability']['evidence']='changed'; self.blocked('STALE_CONFIRMATION',validate_generation,self.job,self.folder)
    def test_reference_replacement_detected(self):
        prompt_ready(self.job,self.folder); (self.folder/'inputs/reference.png').write_bytes(PNG+b'changed'); self.blocked('SOURCE_CHANGED',validate_generation,self.job,self.folder)
    def test_path_escape_blocked(self):
        outside=self.folder.parent/'outside.txt'; outside.write_text('x'); self.blocked('PATH',local_file,self.folder,'../outside.txt')
    def test_missing_prompt_blocks_begin(self):
        prompt_ready(self.job,self.folder); self.job['prompts']={}; self.blocked('PROMPT',begin,self.job,self.folder)
    def test_changed_prompt_blocks_begin(self):
        prompt_ready(self.job,self.folder); local_file(self.folder,self.job['prompts']['01-main']['path']).write_text('changed'); self.blocked('PROMPT',begin,self.job,self.folder)
    def test_fake_image_blocked(self):
        prompt_ready(self.job,self.folder); begin(self.job,self.folder); fake=self.folder/'inputs/fake.png'; fake.write_text('not image'); self.blocked('IMAGE_FILE',record_image,self.job,self.folder,'01-main',fake,'gpt-image-2')
    def test_mismatched_actual_model_blocked(self):
        prompt_ready(self.job,self.folder); begin(self.job,self.folder); self.blocked('MODEL_RESULT',record_image,self.job,self.folder,'01-main',self.folder/'inputs/reference.png','other')
    def test_duplicate_record_blocked(self):
        prompt_ready(self.job,self.folder); generated(self.job,self.folder); self.blocked('STATE',record_image,self.job,self.folder,'01-main',self.folder/'inputs/reference.png','gpt-image-2')
    def test_pass_with_issues_blocked(self):
        prompt_ready(self.job,self.folder); generated(self.job,self.folder); r=report(self.job,status='FAIL'); r['status']='PASS'; self.blocked('QC_CONTRADICTION',validate_qc,r,self.job,self.folder)
    def test_stale_qc_hash_blocked(self):
        prompt_ready(self.job,self.folder); generated(self.job,self.folder); r=report(self.job); r['asset_sha256']='0'*64; self.blocked('QC_STALE',validate_qc,r,self.job,self.folder)
    def test_all_images_must_pass(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/'job'; job=ready_job(folder,2); prompt_ready(job,folder); generated(job,folder)
            apply_report(job,folder,report(job)); self.assertEqual(job['state'],'QC')
            self.blocked('QC_INCOMPLETE',aggregate_qc,job,folder)
            apply_report(job,folder,report(job,'02-detail')); self.assertEqual(job['state'],'FINAL'); validate_job(job,folder)
    def test_repairs_only_failed_images(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/'job'; job=ready_job(folder,2); prompt_ready(job,folder); generated(job,folder)
            apply_report(job,folder,report(job)); apply_report(job,folder,report(job,'02-detail','FAIL'))
            self.blocked('REPAIR_SCOPE',add_prompt,job,folder,'01-main',folder/'inputs/prompt.txt')
            old=copy.deepcopy(job['artifacts']['01-main']); add_prompt(job,folder,'02-detail',folder/'inputs/prompt.txt')
            self.assertEqual(begin(job,folder)['image_ids'],['02-detail']); record_image(job,folder,'02-detail',folder/'inputs/reference.png','gpt-image-2')
            apply_report(job,folder,report(job,'02-detail')); self.assertEqual(job['state'],'FINAL'); self.assertEqual(old,job['artifacts']['01-main'])
    def test_repair_limit_and_version_retention(self):
        prompt_ready(self.job,self.folder); generated(self.job,self.folder)
        for _ in range(3):
            apply_report(self.job,self.folder,report(self.job,status='FAIL'))
            add_prompt(self.job,self.folder,'01-main',self.folder/'inputs/prompt.txt'); generated(self.job,self.folder)
        apply_report(self.job,self.folder,report(self.job,status='FAIL')); add_prompt(self.job,self.folder,'01-main',self.folder/'inputs/prompt.txt')
        self.blocked('REPAIR_LIMIT',begin,self.job,self.folder)
        self.assertEqual(len(list((self.folder/'outputs').glob('*.png'))),4)
    def test_final_asset_mutation_blocked(self):
        prompt_ready(self.job,self.folder); generated(self.job,self.folder); apply_report(self.job,self.folder,report(self.job))
        local_file(self.folder,self.job['artifacts']['01-main']['path']).write_bytes(PNG+b'changed'); self.blocked('QC_STALE',validate_job,self.job,self.folder)
    def test_final_requires_new_job(self):
        prompt_ready(self.job,self.folder); generated(self.job,self.folder); apply_report(self.job,self.folder,report(self.job)); self.blocked('STATE',invalidate,self.job,'change')
    def test_concurrent_writer_blocked(self):
        with locked(self.folder):
            with self.assertRaises(Blocked):
                with locked(self.folder): pass
    def test_schema_rejects_string_boolean(self):
        self.job['generation']['confirmed']='true'; self.blocked('SCHEMA',schema_validate,self.job,'image-job')
    def test_cli_confirmation_and_delivery(self):
        save(self.folder,self.job)
        def cli(*args):
            result=subprocess.run([sys.executable,str(ROOT/'scripts/workflow.py'),'--job',str(self.folder),*args],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stderr)
            return result
        cli('confirm','--text','确认','--actor','cli-test'); cli('advance','PLANNING')
        source=self.folder/'inputs/prompt.txt'; source.write_text('Test preservation prompt.',encoding='utf-8')
        cli('prompt','--image','01-main','--file',str(source)); cli('advance','PROMPT_READY'); cli('begin')
        cli('record','--image','01-main','--file',str(self.folder/'inputs/reference.png'),'--reported-model','gpt-image-2')
        job=read(self.folder/'image-job.json'); r=report(job); rp=self.folder/'inputs/review.json'; rp.write_text(json.dumps(r),encoding='utf-8')
        cli('qc','--file',str(rp)); result=cli('export'); self.assertTrue((Path(result.stdout.strip())/'manifest.json').is_file())

if __name__=='__main__': unittest.main()
