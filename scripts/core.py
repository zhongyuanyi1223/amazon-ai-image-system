"""Local workflow invariants. Native image calls remain the Director's responsibility."""
from __future__ import annotations
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = {'确认', '确认生成', '开始生成', '可以生成'}
ACTIVE = {'LOCKED','PLANNING','PROMPT_READY','GENERATING','QC','REVISION','FINAL'}
EDGES = {
    'INIT': {'COLLECTING'}, 'COLLECTING': {'ANALYZING'},
    'ANALYZING': {'VALIDATING','COLLECTING'},
    'VALIDATING': {'WAITING_FOR_CONFIRMATION','COLLECTING'},
    'WAITING_FOR_CONFIRMATION': {'LOCKED','COLLECTING'},
    'LOCKED': {'PLANNING','COLLECTING'}, 'PLANNING': {'PROMPT_READY','COLLECTING'},
    'PROMPT_READY': {'GENERATING','COLLECTING'}, 'GENERATING': {'QC','COLLECTING'},
    'QC': {'FINAL','REVISION','COLLECTING'}, 'REVISION': {'GENERATING','COLLECTING'},
    'FINAL': set(), 'CANCELLED': set(),
}
P0 = ['product_identity','structure','quantity','color','supported_claims','immutable_features','reference_images']

class Blocked(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

def require(condition, code, message):
    if not condition:
        raise Blocked(code, message)

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def local_file(folder, relative):
    require(isinstance(relative,str) and relative.strip(), 'PATH', '缺少文件路径。')
    p = (Path(folder) / relative).resolve()
    require(not Path(relative).is_absolute() and p.is_relative_to(Path(folder).resolve()), 'PATH', '素材必须位于当前 Job 内。')
    require(p.is_file(), 'FILE_MISSING', f'文件不存在：{relative}')
    return p

def policy():
    content = (ROOT/'config/model-policy.md').read_text(encoding='utf-8')
    blocks = re.findall(r'```yaml\s*\n(.*?)```', content, re.S)
    require(len(blocks)==1,'POLICY','模型策略必须有且只有一个 YAML 块。')
    return yaml.safe_load(blocks[0])

def schema_validate(value, name):
    schemas = [read(p) for p in (ROOT/'schemas').glob('*.json')]
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
    selected = read(ROOT/'schemas'/f'{name}.schema.json')
    Draft202012Validator.check_schema(selected)
    errors = sorted(Draft202012Validator(selected, registry=registry).iter_errors(value),key=lambda e:str(e.path))
    require(not errors, 'SCHEMA', '数据格式错误：'+ ('; '.join(f'{list(e.path)}: {e.message}' for e in errors[:3])))

def binding(job):
    g = job['generation']
    return digest({'product':job['product'],'plan':job['plan'],'requirements':job['requirements'],
                   'generation':{k:g[k] for k in ['provider','model','quality','scope','capability','max_revisions']}})

def transition(job, target, event):
    origin = job['state']
    require(target in EDGES[origin] or (target=='CANCELLED' and origin not in {'FINAL','CANCELLED'}), 'STATE', f'不允许状态跳跃：{origin} → {target}')
    job['state'] = target
    job['history'].append({'from':origin,'to':target,'event':event,'at':now()})

def validate_history(job):
    h=job['history']
    require(h and h[0]['from'] is None and h[0]['to']=='INIT','HISTORY','缺少任务创建记录。')
    previous='INIT'
    for entry in h[1:]:
        require(entry['from']==previous, 'HISTORY','状态历史不连续。')
        target=entry['to']
        require(target in EDGES[previous] or (target=='CANCELLED' and previous not in {'FINAL','CANCELLED'}),'HISTORY','状态历史包含非法跳跃。')
        previous=target
    require(previous==job['state'],'HISTORY','当前状态与历史不一致。')

def value_ready(fact, label, allow_empty=False):
    require(fact['status']!='CONFLICT','CONFLICT',f'{label} 的资料存在冲突，请确认。')
    require(fact['status'] in {'CONFIRMED','LOCKED'},'P0',f'请确认 {label}。')
    require(bool(fact['sources']),'SOURCE',f'{label} 缺少事实来源。')
    v=fact['value']
    require(v is not None and (allow_empty or (v!=[] and v!={} and (not isinstance(v,str) or bool(v.strip())))), 'P0',f'{label} 缺少内容。')
    return v

def check_files(job, folder):
    refs=job['product']['reference_images']['value']
    for asset in refs + job['requirements']['source_documents']:
        require(isinstance(asset,dict) and set(asset)>={'path','sha256'},'SOURCE','素材需要 path 与 sha256。')
        p=local_file(folder,asset['path'])
        require(file_hash(p)==asset['sha256'],'SOURCE_CHANGED',f'素材内容已改变：{asset["path"]}')

def validate_ready(job, folder):
    schema_validate(job,'image-job')
    validate_history(job)
    r=job['requirements']; p=job['product']
    for k in ['platform','marketplace','image_type']:
        value_ready(r[k],k)
    require(r['platform']['value']=='Amazon','PLATFORM','V1 仅支持 Amazon。')
    require(r['marketplace']['value']=='US','MARKETPLACE','当前规则包仅支持 US；其他站点需管理员扩展。')
    require(r['image_type']['value'] in {'main','secondary','aplus','image_set'},'IMAGE_TYPE','未知图片类型。')
    require(bool(r['source_documents']),'LISTING','请提供 Listing 或等效产品说明。')
    for k in P0 + (['material'] if r['material_affects_visual'] else []):
        value_ready(p[k],k, allow_empty=(k=='supported_claims'))
    for key,f in p.items():
        require(f['status']!='CONFLICT','CONFLICT',f'{key} 存在未解决冲突。')
    require(type(p['quantity']['value']) is int and p['quantity']['value']>0,'QUANTITY','销售数量必须为正整数。')
    require(isinstance(p['reference_images']['value'],list),'REFERENCE','参考图必须是文件列表。')
    require(isinstance(p['supported_claims']['value'],list),'CLAIM','功能声明必须是列表。')
    require(isinstance(p['immutable_features']['value'],list),'PRODUCT','不可变特征必须是列表。')
    for key in ['product_identity','structure','color']:
        require(isinstance(p[key]['value'],(str,dict,list)),'PRODUCT',f'{key} 类型错误。')
    images=job['plan']['images']; ids=[i['image_id'] for i in images]
    require(len(ids)==len(set(ids)),'PLAN','图片 ID 重复。')
    allowed={'main':{'main'},'secondary':{'secondary','lifestyle','feature','size','detail','comparison','scene'},'aplus':{'aplus'},'image_set':{'main','secondary','lifestyle','feature','size','detail','comparison','scene'}}[r['image_type']['value']]
    require(all(i['type'] in allowed for i in images),'IMAGE_TYPE','方案图型与任务需求不一致。')
    for i in images:
        require(bool(i['evidence']),'EVIDENCE',f'{i["image_id"]} 缺少事实依据。')
        if i['type']=='main':
            require(not i['visible_copy'].strip(),'MAIN_COPY','主图不能添加覆盖文字。')
        if i['type']=='size':
            value_ready(p['dimensions'],'dimensions')
    check_files(job,folder)
    cfg=policy()['image_generation']; g=job['generation']; c=g['capability']
    require(g['provider']==cfg['provider'] and g['quality']==cfg['quality'],'MODEL_POLICY','生成配置偏离项目策略。')
    if g['scope']=='default':
        require(g['model']==cfg['model'],'MODEL_POLICY','默认模型与项目策略不一致。')
    require(c['native_available'] and bool(c['evidence'].strip()),'CAPABILITY','请先核实原生图片工具可用。')
    if c['selectable_model']:
        require(g['model'] in c['available_models'],'MODEL_UNAVAILABLE','当前环境没有证据支持所选模型。')
    else:
        require(g['scope']=='default' and g['model']==cfg['model'],'MODEL_UNAVAILABLE','原生工具不支持指定本次切换模型。')

def validate_confirmation(job):
    g=job['generation']; c=g['confirmation']
    require(g['confirmed'] is True and isinstance(c,dict),'UNCONFIRMED','需要运营明确确认当前图片方案。')
    require(set(c)>={'text','actor','at','digest','native_model_unverified_ack'},'UNCONFIRMED','确认记录不完整。')
    require(c['text'] in ACCEPTED and bool(c['actor'].strip()),'UNCONFIRMED','缺少有效运营确认。')
    require(c['digest']==binding(job),'STALE_CONFIRMATION','产品、方案或生成设置已改变，需要重新确认。')
    if not g['capability']['selectable_model']:
        require(c['native_model_unverified_ack'] is True,'MODEL_DISCLOSURE','需确认接受原生工具实际模型不可核验的限制。')
    for k in P0 + (['material'] if job['requirements']['material_affects_visual'] else []):
        require(job['product'][k]['status']=='LOCKED','LOCK','产品关键字段未锁定。')

def validate_generation(job, folder):
    validate_ready(job,folder)
    validate_confirmation(job)
    require(job['state'] in {'PROMPT_READY','REVISION','GENERATING'},'STATE','当前状态不允许生成。')
    return 'ALLOW'

def confirm(job, folder, text, actor, ack=False):
    require(job['state']=='WAITING_FOR_CONFIRMATION','STATE','先展示并等待确认当前方案。')
    require(text in ACCEPTED and bool(actor.strip()),'UNCONFIRMED','请记录运营的明确确认原话和身份。')
    validate_ready(job,folder)
    if not job['generation']['capability']['selectable_model']:
        require(ack is True,'MODEL_DISCLOSURE','先向运营披露原生工具实际模型不可核验，再记录其接受。')
    for f in job['product'].values():
        if f['status']=='CONFIRMED': f['status']='LOCKED'
    job['generation']['confirmed']=True
    job['generation']['confirmation']={'text':text,'actor':actor,'at':now(),'digest':binding(job),'native_model_unverified_ack':ack}
    transition(job,'LOCKED','operator_confirmation')

def invalidate(job, event):
    require(job['state'] not in {'FINAL','CANCELLED'},'STATE','已结束任务请创建新的 Job。')
    if job['state']!='COLLECTING': transition(job,'COLLECTING',event)
    for f in job['product'].values():
        if f['status']=='LOCKED': f['status']='CONFIRMED'
    job['generation']['confirmed']=False
    job['generation']['confirmation']=None
    job['prompts']={}; job['artifacts']={}; job['qc']={}; job['active_images']=[]

def switch_model(job, model, text):
    require(text in ACCEPTED,'UNCONFIRMED','模型切换需要明确确认。')
    cap=job['generation']['capability']
    require(cap['native_available'] and cap['selectable_model'] and model in cap['available_models'],'MODEL_UNAVAILABLE','当前工具不能选择该模型。')
    invalidate(job,'model_switch_confirmation_invalidated')
    job['generation']['model']=model
    job['generation']['scope']='current_job'

def targets(job):
    if job['state']=='REVISION':
        return [i['image_id'] for i in job['plan']['images'] if job['qc'].get(i['image_id'],{}).get('status')=='FAIL']
    return [i['image_id'] for i in job['plan']['images']]

def check_prompts(job,folder,ids):
    for image_id in ids:
        entry=job['prompts'].get(image_id,{})
        require(entry.get('confirmation_digest')==binding(job),'PROMPT','Prompt 未绑定当前确认。')
        p=local_file(folder,entry.get('path',''))
        require(file_hash(p)==entry.get('sha256'),'PROMPT','Prompt 已被修改，请重新登记。')
        if job['state']=='REVISION':
            require(entry.get('repair_of')==job['artifacts'][image_id]['sha256'],'PROMPT','修复 Prompt 必须绑定失败图片版本。')

def begin(job,folder):
    require(job['state'] in {'PROMPT_READY','REVISION'},'STATE','不能重复开始生成批次。')
    validate_generation(job,folder)
    ids=targets(job)
    require(bool(ids),'REVISION','没有需要生成的图片。')
    check_prompts(job,folder,ids)
    for image_id in ids:
        old=job['artifacts'].get(image_id)
        require(not old or old['revision']<job['generation']['max_revisions'],'REPAIR_LIMIT','修复次数已达上限，请重新规划并确认。')
    job['active_images']=ids
    transition(job,'GENERATING','validated_generation_batch')
    return {'job_id':job['job_id'],'confirmation_digest':binding(job),'image_ids':ids,'requested_model':job['generation']['model'],'native_model_selectable':job['generation']['capability']['selectable_model'],'note':'Director must now invoke the available OpenAI native image tool; this command does not generate images.'}

def validate_qc(report,job,folder):
    schema_validate(report,'qc-result')
    require(report['job_id']==job['job_id'],'QC_JOB','QC 属于另一个任务。')
    image_id=report['image_id']; asset=job['artifacts'].get(image_id)
    require(asset is not None,'QC_ASSET','没有对应的生成图片。')
    require(asset['confirmation_digest']==binding(job),'QC_STALE','图片属于已失效的确认版本。')
    require(report['confirmation_digest']==binding(job),'QC_STALE','QC 绑定的方案已失效。')
    require(report['asset_sha256']==asset['sha256']==file_hash(local_file(folder,asset['path'])),'QC_STALE','QC 与当前图片文件不匹配。')
    checks=report['checks']
    if report['status']=='PASS':
        require(not report['issues'] and all(v=='PASS' for v in checks.values()),'QC_CONTRADICTION','PASS 报告不能包含未解决问题或失败检查项。')
    else:
        require(bool(report['issues']) and any(v=='FAIL' for v in checks.values()),'QC_CONTRADICTION','FAIL 必须说明失败检查项和可执行修复指令。')
    return 'FINAL' if report['status']=='PASS' else 'REVISION'

def aggregate_qc(job,folder):
    ids=[i['image_id'] for i in job['plan']['images']]
    require(set(job['artifacts'])==set(ids),'QC_INCOMPLETE','尚未生成全部方案图片。')
    require(set(job['qc'])==set(ids),'QC_INCOMPLETE','尚未完成全部图片 QC。')
    for i in ids: validate_qc(job['qc'][i],job,folder)
    return 'FINAL' if all(job['qc'][i]['status']=='PASS' for i in ids) else 'REVISION'

def validate_job(job,folder):
    schema_validate(job,'image-job'); validate_history(job)
    if job['state'] in ACTIVE:
        validate_ready(job,folder); validate_confirmation(job)
    if job['state']=='FINAL': require(aggregate_qc(job,folder)=='FINAL','QC','没有全部 PASS，不能交付。')
    return 'VALID'
