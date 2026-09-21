"""Director CLI. All paths in stored jobs are portable, relative to the Job folder."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from core import (ROOT, Blocked, require, read, now, file_hash, local_file, policy,
                  schema_validate, transition, validate_ready, validate_confirmation,
                  validate_generation, validate_job, confirm, invalidate, switch_model,
                  binding, begin, validate_qc, aggregate_qc, check_prompts)

def atomic_json(path,value):
    p=Path(path); tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.replace(tmp,p)
    finally:
        if tmp.exists(): tmp.unlink()

@contextmanager
def locked(folder):
    lock=folder/'.workflow.lock'
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise Blocked('BUSY','另一个进程正在修改此 Job；若此前异常退出，请管理员检查后清理锁。')
    try:
        os.write(fd,str(os.getpid()).encode()); os.close(fd)
        yield
    finally: lock.unlink(missing_ok=True)

def save(folder,job):
    schema_validate(job,'image-job')
    # Canonical record is replaced atomically. Sidecars are derived snapshots.
    atomic_json(folder/'image-job.json',job)
    atomic_json(folder/'product-card.json',job['product'])
    atomic_json(folder/'image-plan.json',job['plan'])

def create(folder,sku):
    require(not folder.exists(),'EXISTS','目录已存在，使用新的唯一 Job 目录。')
    job=read(ROOT/'templates/image-job.template.json')
    job['job_id']=folder.name; job['sku']=sku
    cfg=policy()['image_generation']
    job['generation'].update(cfg)
    job['history'][0]['at']=now()
    folder.mkdir(parents=True)
    for name in ['inputs','prompts','qc','outputs','history']:(folder/name).mkdir()
    save(folder,job)
    return job

def add_prompt(job,folder,image_id,source):
    require(job['state'] in {'PLANNING','PROMPT_READY','REVISION'},'STATE','此阶段不能登记 Prompt。')
    validate_ready(job,folder); validate_confirmation(job)
    require(image_id in {i['image_id'] for i in job['plan']['images']},'IMAGE_ID','未知图片 ID。')
    require(source.is_file() and source.read_text(encoding='utf-8').strip(),'PROMPT','Prompt 文件为空或不存在。')
    repair=None
    if job['state']=='REVISION':
        require(job['qc'].get(image_id,{}).get('status')=='FAIL','REPAIR_SCOPE','只能修改 QC 失败的图片。')
        repair=job['artifacts'][image_id]['sha256']
    dest=folder/'prompts'/f'{image_id}-{uuid.uuid4().hex[:12]}.txt'
    shutil.copyfile(source,dest)
    job['prompts'][image_id]={'path':dest.relative_to(folder).as_posix(),'sha256':file_hash(dest),'confirmation_digest':binding(job),'repair_of':repair}

def record_image(job,folder,image_id,source,reported_model=None):
    require(job['state']=='GENERATING' and image_id in job['active_images'],'STATE','此图片不在当前待生成批次。')
    validate_generation(job,folder)
    require(source.is_file(),'FILE_MISSING','请保存实际生成图片后再登记。')
    data=source.read_bytes()
    valid=(source.suffix.lower()=='.png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or (source.suffix.lower() in {'.jpg','.jpeg'} and data.startswith(b'\xff\xd8\xff')) or (source.suffix.lower()=='.webp' and data[:4]==b'RIFF' and data[8:12]==b'WEBP')
    require(valid,'IMAGE_FILE','文件格式或图片签名不匹配；不允许用文字文件冒充生成图片。')
    g=job['generation']
    if g['capability']['selectable_model']:
        require(reported_model==g['model'],'MODEL_RESULT','工具实际模型与确认模型不匹配或无法核验。')
    old=job['artifacts'].get(image_id); revision=old['revision']+1 if old else 0
    dest=folder/'outputs'/f'{image_id}-v{revision+1:02d}-{uuid.uuid4().hex[:8]}{source.suffix.lower()}'
    shutil.copyfile(source,dest)
    job['artifacts'][image_id]={'path':dest.relative_to(folder).as_posix(),'sha256':file_hash(dest),'revision':revision,'reported_model':reported_model,'recorded_at':now(),'confirmation_digest':binding(job)}
    job['qc'].pop(image_id,None)
    job['active_images'].remove(image_id)
    if not job['active_images']: transition(job,'QC','batch_images_recorded')

def apply_report(job,folder,report):
    require(job['state']=='QC','STATE','当前不是 QC 阶段。')
    validate_ready(job,folder); validate_confirmation(job)
    validate_qc(report,job,folder)
    job['qc'][report['image_id']]=report
    dest=folder/'qc'/f'{report["image_id"]}-{uuid.uuid4().hex[:12]}.json'
    atomic_json(dest,report)
    if set(job['qc'])=={i['image_id'] for i in job['plan']['images']}:
        target=aggregate_qc(job,folder)
        transition(job,target,'aggregate_visual_qc')

def summary(job):
    p=job['product']; g=job['generation']
    return {'标题':'Amazon图片生产确认','平台':job['requirements']['platform']['value'],
            '站点':job['requirements']['marketplace']['value'],'产品':p['product_identity']['value'],
            '产品不可改变':{k:v['value'] for k,v in p.items() if k!='reference_images'},
            '图片方案':job['plan'],'默认或本次模型':g['model'],'质量意向':g['quality'],
            '工具说明':'工具支持选择所列模型；生成后核验工具返回标识。' if g['capability']['selectable_model'] else '原生工具未提供可选择的模型/质量参数，实际模型与档位不可保证；需明确接受此限制。',
            '问题':'是否确认生成？'}

def parser():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--job',required=True,type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('init'); q.add_argument('--sku',required=True)
    q=sub.add_parser('advance'); q.add_argument('state',choices=['COLLECTING','ANALYZING','VALIDATING','WAITING_FOR_CONFIRMATION','PLANNING','PROMPT_READY','CANCELLED'])
    q=sub.add_parser('update'); q.add_argument('section',choices=['product','plan','requirements','capability']); q.add_argument('file',type=Path)
    sub.add_parser('summary')
    q=sub.add_parser('confirm'); q.add_argument('--text',required=True); q.add_argument('--actor',required=True); q.add_argument('--accept-unverified-native-model',action='store_true')
    q=sub.add_parser('switch-model'); q.add_argument('--model',required=True); q.add_argument('--text',required=True)
    q=sub.add_parser('prompt'); q.add_argument('--image',required=True); q.add_argument('--file',required=True,type=Path)
    sub.add_parser('begin')
    q=sub.add_parser('record'); q.add_argument('--image',required=True); q.add_argument('--file',required=True,type=Path); q.add_argument('--reported-model')
    q=sub.add_parser('qc'); q.add_argument('--file',required=True,type=Path)
    sub.add_parser('validate'); sub.add_parser('export')
    return p

def main():
    a=parser().parse_args(); folder=a.job.resolve()
    try:
        if a.command=='init':
            create(folder,a.sku); print('CREATED'); return 0
        require(folder.is_dir(),'JOB','Job 目录不存在。')
        with locked(folder):
            job=read(folder/'image-job.json'); schema_validate(job,'image-job')
            result='OK'
            if a.command=='summary': result=summary(job)
            elif a.command=='validate': result=validate_job(job,folder)
            elif a.command=='update':
                value=read(a.file)
                if a.section in {'product','plan'}: schema_validate(value,'product' if a.section=='product' else 'image-plan')
                invalidate(job,'content_changed_confirmation_invalidated')
                if a.section=='capability': job['generation']['capability']=value
                else: job[a.section]=value
                # Imported LOCKED values are never accepted as operator approval.
                for f in job['product'].values():
                    if f['status']=='LOCKED': f['status']='CONFIRMED'
            elif a.command=='advance':
                if a.state=='WAITING_FOR_CONFIRMATION': validate_ready(job,folder)
                if a.state in {'PLANNING','PROMPT_READY'}:
                    validate_ready(job,folder); validate_confirmation(job)
                if a.state=='PROMPT_READY': check_prompts(job,folder,[i['image_id'] for i in job['plan']['images']])
                transition(job,a.state,'director_step')
            elif a.command=='confirm': confirm(job,folder,a.text,a.actor,a.accept_unverified_native_model)
            elif a.command=='switch-model': switch_model(job,a.model,a.text)
            elif a.command=='prompt': add_prompt(job,folder,a.image,a.file)
            elif a.command=='begin': result=begin(job,folder)
            elif a.command=='record': record_image(job,folder,a.image,a.file,a.reported_model)
            elif a.command=='qc': apply_report(job,folder,read(a.file))
            elif a.command=='export':
                validate_job(job,folder); require(job['state']=='FINAL','STATE','仅 FINAL 可以导出。')
                dest=folder/'outputs'/('delivery-'+uuid.uuid4().hex[:12]); dest.mkdir()
                manifest={}
                for image_id,asset in job['artifacts'].items():
                    src=local_file(folder,asset['path']); name=image_id+src.suffix
                    shutil.copyfile(src,dest/name); manifest[name]={'sha256':asset['sha256'],'qc':'PASS'}
                atomic_json(dest/'manifest.json',manifest); result=str(dest)
            if a.command not in {'summary','validate','export'}:
                atomic_json(folder/'history'/(uuid.uuid4().hex+'.json'),job)
                save(folder,job)
            print(json.dumps(result,ensure_ascii=False,indent=2) if isinstance(result,dict) else result)
        return 0
    except (Blocked, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({'status':'BLOCKED','code':getattr(e,'code','INPUT'),'message':str(e)},ensure_ascii=False),file=sys.stderr)
        return 1

if __name__=='__main__': sys.exit(main())
