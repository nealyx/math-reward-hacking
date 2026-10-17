"""Resume the fixed 21x500 local diagnostic using unchanged frozen pilot inference.

Only verified missing keys are generated. Canonical rows are immutable atomic
commits; all original journals, including partial/error attempts, are preserved.
"""
import argparse
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import time
import traceback
import uuid

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent/"pilot"
TIMING=PILOT/"attempts/001_fp16_mps/timing"


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


S=module(HERE/"run_storage.py","full_storage")


def utc():return datetime.now(timezone.utc).isoformat()


def rendered_ids(tokenizer,messages):
    encoded=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
    ids=encoded["input_ids"] if isinstance(encoded,Mapping) else encoded
    if not isinstance(ids,list) or not all(type(i) is int for i in ids):
        raise ValueError("Expected a flat rendered prompt token-ID list")
    return ids


def checked_pilot():
    frozen=json.loads((PILOT/"freeze.json").read_text())
    if json.loads((TIMING/"source_freeze.json").read_text())!=frozen:
        raise ValueError("Timing/live pilot freeze mismatch")
    for name,want in frozen["source_sha256"].items():
        if S.sha(PILOT/name)!=want:raise ValueError(f"Frozen pilot source changed: {name}")
    for name,want in frozen["model_files_sha256"].items():
        if S.sha(name)!=want:raise ValueError(f"Frozen model/tokenizer changed: {name}")
    preserved=json.loads((PILOT/"artifact_manifest.json").read_text())
    for name,item in preserved["artifacts"].items():
        if S.sha(PILOT/name)!=item["sha256"]:raise ValueError(f"Pilot artifact changed: {name}")
    return frozen


def host(p):
    return {"platform":platform.platform(),"machine":platform.machine(),"python":platform.python_version(),
            "packages":{n:p.importlib.metadata.version(n) for n in ("torch","transformers","peft","tokenizers","accelerate")},
            "device":"mps","dtype":"float16","attention_implementation":"eager",
            "deterministic_algorithms":p.torch.are_deterministic_algorithms_enabled(),
            "deterministic_warn_only":p.torch.is_deterministic_algorithms_warn_only_enabled(),
            "mps_cpu_fallback_env":os.environ["PYTORCH_ENABLE_MPS_FALLBACK"],
            "memory_fraction":.8,"recommended_max_memory_bytes":p.torch.mps.recommended_max_memory(),
            "hardware":subprocess.check_output(["/usr/sbin/sysctl","-n","hw.model","hw.memsize","machdep.cpu.brand_string"],text=True).strip().splitlines(),
            "stage":"full","seed":p.SEED,"metadata_self_test":p.metadata_self_test()}


def compare_host(observed):
    expected=json.loads((TIMING/"host.json").read_text())
    names=("platform","machine","python","packages","device","dtype","attention_implementation",
           "deterministic_algorithms","deterministic_warn_only","mps_cpu_fallback_env","memory_fraction","hardware","seed")
    changed=[n for n in names if expected[n]!=observed[n]]
    if changed:raise ValueError(f"Environment/settings differ from timing pilot: {changed}")


def load_model(p,label,adapter,telemetry,purpose):
    # These are the same constructor arguments, conversions and eval settings
    # used in frozen run_pilot.main; generation itself is imported unchanged.
    gc.collect();p.torch.mps.empty_cache();p.torch.mps.synchronize()
    started=time.perf_counter()
    with p.Memory() as memory:
        model=p.AutoModelForCausalLM.from_pretrained(p.BASE,local_files_only=True,trust_remote_code=False,
                                                   dtype=p.torch.float16,attn_implementation="eager")
        if adapter:model=p.PeftModel.from_pretrained(model,adapter,is_trainable=False,autocast_adapter_dtype=False,local_files_only=True)
        model=model.to(device="mps",dtype=p.torch.float16)
        model.eval();p.torch.mps.synchronize()
    dtypes=Counter(str(param.dtype) for param in model.parameters() if param.is_floating_point())
    devices=Counter(str(param.device) for param in model.parameters())
    if set(dtypes)!={"torch.float16"} or not all(d.startswith("mps") for d in devices):
        raise ValueError(f"Precision/device mismatch: {label}")
    adapter_hash=S.sha(adapter/"adapter_model.safetensors") if adapter else None
    p.append(telemetry/"loading.jsonl",{"model":label,"purpose":purpose,"loading_seconds":time.perf_counter()-started,
             "parameter_dtypes":dict(dtypes),"parameter_devices":dict(devices),"adapter_sha256":adapter_hash,**memory.result()})
    return model,adapter_hash


def configuration(p,model,label,cap,expected,telemetry):
    config=p.prepare_config(model,cap)
    digest=hashlib.sha256(config.to_json_string(use_diff=False).encode()).hexdigest()
    old=expected[label,cap]
    if config.to_dict()!=old["configuration"] or digest!=old["sha256"]:
        raise ValueError(f"Resolved generation configuration changed: {label}/{cap}")
    p.append(telemetry/"generation_configs.jsonl",{"model":label,"cap":cap,"configuration":config.to_dict(),"sha256":digest})
    return config


def origin(row,source,kind,line=1):
    return {**row,"full_origin":{"kind":kind,"source_file":os.path.relpath(source,HERE),
            "source_file_sha256":S.sha(source),"source_line1based":line}}


def main(preflight_only):
    started=time.perf_counter();start_utc=utc()
    with S.writer_lock(HERE/".writer.lock"):
        frozen=checked_pilot()
        sources={name:S.sha(HERE/name) for name in ("run_full.py","run_storage.py","verify_full.py")}
        proposed={"schema":"arithmetic-full-local-freeze-1","pilot_freeze":frozen,"run_source_sha256":sources,
                  "pilot_freeze_sha256":S.sha(PILOT/"freeze.json"),
                  "pilot_artifact_manifest_sha256":S.sha(PILOT/"artifact_manifest.json"),
                  "timing_responses_sha256":S.sha(TIMING/"responses.jsonl"),
                  "timing_generation_configs_sha256":S.sha(TIMING/"generation_configs.json"),
                  "timing_attempt":"001_fp16_mps","expected_records":10500,"reuse_expected":420,
                  "models":["Base","robust_201","proxy_201","robust_202","proxy_202","robust_203","proxy_203"],
                  "caps":[128,256,512],"example_ids":list(range(500)),
                  "inference":"Direct call to unchanged pilot.run_pilot.generate/prepare_config; same load arguments, hardware/environment and settings.",
                  "authorization":"User explicitly authorized full local diagnostic, reuse verified timing only, no training/paid compute/expansion."}
        freeze_path=HERE/"run_freeze.json"
        if freeze_path.exists():
            if json.loads(freeze_path.read_text())!=proposed:raise ValueError("Full-run freeze/source changed; refuse resume")
        else:S.dump_new(freeze_path,proposed)
        p=module(PILOT/"run_pilot.py","unchanged_frozen_pilot")
        V=module(HERE/"verify_full.py","full_artifact_verifier")
        p.torch.set_num_threads(4);p.torch.use_deterministic_algorithms(True,warn_only=False)
        p.torch.mps.set_per_process_memory_fraction(.8)
        p.torch.manual_seed(p.SEED);p.torch.mps.manual_seed(p.SEED);random.seed(p.SEED)
        if not p.torch.backends.mps.is_available():raise RuntimeError("MPS unavailable")
        observed=host(p);compare_host(observed)
        sid="session_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_")+uuid.uuid4().hex[:8]
        telemetry=HERE/"telemetry"/sid;telemetry.mkdir(parents=True,exist_ok=False)
        S.dump_new(telemetry/"host.json",observed)
        S.dump_new(telemetry/"session.json",{"start_utc":start_utc,"session_id":sid,"preflight_only":preflight_only,
                   "pid":os.getpid(),"python_executable":os.path.realpath(os.sys.executable),"run_freeze_sha256":S.sha(freeze_path)})
        data=V.read_rows(PILOT/"preparation/development.jsonl")
        if len(data)!=500 or [r["problem_id"] for r in data]!=list(range(500)):
            raise ValueError("Frozen data order/coverage changed")
        data_by_id={r["problem_id"]:r for r in data}
        expected_list=json.loads((TIMING/"generation_configs.json").read_text())
        expected={(r["model"],r["cap"]):r for r in expected_list}
        if len(expected_list)!=21 or len(expected)!=21:raise ValueError("Bad pilot config matrix")
        config_hashes={k:r["sha256"] for k,r in expected.items()}
        adapter_hashes={label:S.sha(a/"adapter_model.safetensors") if a else None for label,a in p.MODELS}
        if json.loads((p.BASE/"generation_config.json").read_text())!=json.loads((TIMING/"base_generation_config.json").read_text()):
            raise ValueError("Base generation configuration differs from timing")
        tokenizer=p.AutoTokenizer.from_pretrained(p.BASE,local_files_only=True,trust_remote_code=False)
        if tokenizer.pad_token_id is None:tokenizer.pad_token_id=151643

        def validate(row):
            result=V.verify_records([row],{row["problem_id"]:data_by_id[row["problem_id"]]},tokenizer,
                    config_hashes,adapter_hashes,p.EX,require_complete=False,base_revision=p.BASE.name)
            if not result["pass"]:raise ValueError(f"Record failed verification: {result['errors']}")

        def check_prefix(row):
            for other_cap in p.CAPS:
                other=existing.get((row["model"],other_cap,row["problem_id"]))
                if other is None:continue
                a,b=(other,row) if other_cap<row["max_new_tokens"] else (row,other)
                aa,bb=a["generated_token_ids"],b["generated_token_ids"]
                if aa!=bb[:len(aa)] or (a["stopping_reason"].startswith("eos") and aa!=bb):
                    raise ValueError(f"Independent prefix mismatch: {S.key(row)} / {other_cap}")

        # Verify the complete source timing grid BEFORE permitting any reuse.
        timing_rows=V.read_rows(TIMING/"responses.jsonl")
        if len(timing_rows)!=420 or any(r["phase"]!="timing" or r["problem_id"] not in range(20) for r in timing_rows):
            raise ValueError("Timing source phases/coverage invalid")
        check=V.verify_records(timing_rows,data_by_id,tokenizer,config_hashes,adapter_hashes,p.EX,
                               require_complete=False,base_revision=p.BASE.name)
        if not check["pass"] or check["unique_keys"]!=420:raise ValueError(f"Timing reuse gate failed: {check['errors']}")
        S.dump_new(telemetry/"timing_reuse_gate.json",check)
        # Verify saved tokenizers on ALL 500 rendered inputs without generating.
        ids_by_example=[]
        for item in data:
            messages=[{"role":"system","content":"You are a helpful mathematical assistant."},{"role":"user","content":item["prompt"]}]
            ids_by_example.append(rendered_ids(tokenizer,messages))
        tokenizer_checks=[]
        for label,adapter in p.MODELS:
            other=tokenizer if adapter is None else p.AutoTokenizer.from_pretrained(adapter,local_files_only=True,trust_remote_code=False)
            differences=[]
            for item,want in zip(data,ids_by_example):
                messages=[{"role":"system","content":"You are a helpful mathematical assistant."},{"role":"user","content":item["prompt"]}]
                if rendered_ids(other,messages)!=want:differences.append(item["problem_id"])
            tokenizer_checks.append({"model":label,"n":500,"mismatch_ids":differences})
            if differences:raise ValueError(f"Tokenizer mismatch: {label}")
            if adapter is not None:del other
        S.dump_new(telemetry/"tokenizers.json",{"checks":tokenizer_checks,"ordered_prompt_ids_sha256":hashlib.sha256(json.dumps(ids_by_example).encode()).hexdigest()})
        del ids_by_example
        # No completions here: prove all seven model/config combinations first.
        if not (HERE/"preflight_complete.json").exists():
            for label,adapter in p.MODELS:
                model,_=load_model(p,label,adapter,telemetry,"initial_preflight_no_inference")
                for cap in p.CAPS:configuration(p,model,label,cap,expected,telemetry)
                del model;gc.collect();p.torch.mps.empty_cache();p.torch.mps.synchronize()
            S.dump_new(HERE/"preflight_complete.json",{"pass":True,"run_freeze_sha256":S.sha(freeze_path),"telemetry_session":sid,"completed_utc":utc(),"no_completions_generated":True})
        elif json.loads((HERE/"preflight_complete.json").read_text())["run_freeze_sha256"]!=S.sha(freeze_path):
            raise ValueError("Preflight freeze changed")
        records_dir=HERE/"records";records_dir.mkdir(exist_ok=True)
        scratch=HERE/"commits"/sid
        existing=S.read_committed(records_dir)
        for line,row in enumerate(timing_rows,1):
            record_key=S.key(row)
            enriched=origin(row,TIMING/"responses.jsonl","timing_reuse",line)
            if record_key in existing:
                if existing[record_key]!=enriched:raise ValueError("Existing timing reuse differs")
            else:S.publish(records_dir,scratch,enriched);existing[record_key]=enriched
        # Gate every previously committed record and its preserved source bytes.
        preflight=V.main(HERE,telemetry/"committed_preflight.json",allow_incomplete=True)
        if not preflight["pass"]:raise ValueError("Committed record verification failed")
        recovered=0;ignored_journals=0
        for source in sorted((HERE/"journals").glob("**/responses.jsonl")):
            try:row=S.read_one(source)
            except (ValueError,json.JSONDecodeError) as exc:
                p.append(telemetry/"events.jsonl",{"event":"preserved_partial_journal","source":str(source.relative_to(HERE)),"error":repr(exc)})
                ignored_journals+=1;continue
            if row.get("error") is not None or row.get("stopping_reason")=="error":
                p.append(telemetry/"events.jsonl",{"event":"preserved_error_journal","source":str(source.relative_to(HERE)),"record_key":list(S.key(row)),"error":row.get("error")})
                ignored_journals+=1;continue
            if S.key(row) in existing:continue
            if row.get("phase")!="full":raise ValueError("Unexpected journal phase")
            validate(row)
            check_prefix(row)
            enriched=origin(row,source,"full_generation")
            S.publish(records_dir,scratch,enriched);existing[S.key(row)]=enriched;recovered+=1
        if preflight_only:
            S.dump_new(telemetry/"summary.json",{"start_utc":start_utc,"end_utc":utc(),"elapsed_seconds":time.perf_counter()-started,
                       "preflight_only":True,"generated_count":0,"recovered_count":recovered,"committed_count":len(existing),"pass":True})
            print(json.dumps({"preflight_pass":True,"reused":420,"committed":len(existing),"remaining":10500-len(existing)}),flush=True)
            return
        generated=0
        try:
            for label,adapter in p.MODELS:
                model_missing=any((label,cap,item["problem_id"]) not in existing for cap in p.CAPS for item in data)
                if not model_missing:continue
                model,adapter_hash=load_model(p,label,adapter,telemetry,"missing_record_generation")
                for cap in p.CAPS:
                    missing=[item for item in data if (label,cap,item["problem_id"]) not in existing]
                    if not missing:continue
                    config=configuration(p,model,label,cap,expected,telemetry)
                    block_started=time.perf_counter();block=[]
                    with p.Memory() as memory:
                        for item in missing:
                            record_key=(label,cap,item["problem_id"])
                            journal=HERE/"journals"/sid/f"{label}__{cap}"/f"{item['problem_id']:04d}"
                            journal.mkdir(parents=True,exist_ok=False)
                            # The frozen generation function, unchanged arguments
                            # except phase label and output destination.
                            row=p.generate(model,tokenizer,item,label,config,"full",journal,adapter_hash)
                            validate(row)
                            # Detect cap-prefix failures immediately when both
                            # independent generations have become available.
                            check_prefix(row)
                            enriched=origin(row,journal/"responses.jsonl","full_generation")
                            S.publish(records_dir,scratch,enriched);existing[record_key]=enriched
                            block.append(row);generated+=1
                            if len(block)%5==0 or len(block)==len(missing):
                                print(json.dumps({"utc":utc(),"model":label,"cap":cap,"new_in_cell":len(block),
                                      "missing_in_cell":len(missing),"committed_total":len(existing),"target_total":10500,
                                      "block_seconds":round(time.perf_counter()-block_started,2)}),flush=True)
                    p.append(telemetry/"cells.jsonl",{"model":label,"cap":cap,"n":len(block),"cell_seconds":time.perf_counter()-block_started,
                             "generation_seconds":sum(r["generation_seconds"] for r in block),"record_seconds":sum(r["record_seconds"] for r in block),
                             "actual_generated_tokens":sum(r["generated_token_count"] for r in block),
                             "stopping_counts":dict(Counter(r["stopping_reason"] for r in block)),"errors":0,**memory.result()})
                del model;gc.collect();p.torch.mps.empty_cache();p.torch.mps.synchronize()
            final=V.main(HERE,telemetry/"final_verification.json",allow_incomplete=False)
            S.dump_new(telemetry/"summary.json",{"start_utc":start_utc,"end_utc":utc(),"elapsed_seconds":time.perf_counter()-started,
                       "preflight_only":False,"generated_count":generated,"recovered_count":recovered,"ignored_journals":ignored_journals,
                       "committed_count":len(existing),"reused_count":420,"pass":final["pass"]})
            print(json.dumps({"complete":True,"committed":len(existing),"generated_this_session":generated,"pass":final["pass"]}),flush=True)
        except BaseException as exc:
            S.dump_new(telemetry/"failure.json",{"utc":utc(),"error":repr(exc),"traceback":traceback.format_exc(),
                       "elapsed_seconds":time.perf_counter()-started,"generated_count":generated,"committed_count":len(existing),
                       "resume":"Re-run unchanged entry point; verified journal recovery precedes generation of missing keys."})
            raise


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-only",action="store_true")
    args=parser.parse_args();main(args.preflight_only)
