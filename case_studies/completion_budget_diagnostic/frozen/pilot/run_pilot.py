"""Offline local inference only: 63 smoke cells/replays, or 420 timing rows.

There is deliberately no full-matrix or training mode. Every attempt is exclusive.
"""
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

import argparse
import copy
import ctypes
import gc
import hashlib
import importlib.metadata
import importlib.util
import itertools
import json
import platform
import random
import resource
import statistics
import subprocess
import threading
import time
import traceback
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = Path.home()/".cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/7ae557604adf67be50417f59c2c2f167def9a775"
SPEC = importlib.util.spec_from_file_location("terminal_extractor", HERE/"terminal_extractor.py")
EX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EX)
CAPS = (128,256,512)
EOS = (151645,151643)
SEED = 71448
MODELS = [("Base", None)] + [(f"{c}_{s}", ROOT/f"experiments/milestone3/{c}_seed_{s}/final_model") for s in (201,202,203) for c in ("robust","proxy")]


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def dump(path,obj):
    with path.open("x") as f:
        json.dump(obj,f,indent=2,allow_nan=False)
        f.write("\n")


def append(path,obj):
    with path.open("a") as f:
        f.write(json.dumps(obj,allow_nan=False)+"\n")
        f.flush()
        os.fsync(f.fileno())


def stopping(ids,cap,eos=EOS):
    positions=[i for i,t in enumerate(ids) if t in eos]
    first=positions[0] if positions else None
    count=first+1 if first is not None else len(ids)
    if first is not None:
        reason="eos_at_limit" if count==cap else "eos_before_limit"
    else:
        reason="token_limit_without_eos" if len(ids)==cap else "unexpected_stop"
    return {"first_eos_index_zero_based":first,"generated_token_count":count,
            "raw_new_sequence_length":len(ids),"stopping_reason":reason,
            "eos_at_limit":reason=="eos_at_limit","cap_without_eos":reason=="token_limit_without_eos",
            "ids_after_first_eos":0 if first is None else len(ids)-first-1}


def metadata_self_test():
    cases=[([7,8],2,"token_limit_without_eos"),([7,151645],2,"eos_at_limit"),
           ([151643],2,"eos_before_limit"),([7],2,"unexpected_stop")]
    for ids,cap,expected in cases:
        assert stopping(ids,cap)["stopping_reason"]==expected
    return {"synthetic_stopping_cases":len(cases),"pass":True}


class TaskInfo(ctypes.Structure):
    _fields_=[("virtual",ctypes.c_uint64),("resident",ctypes.c_uint64),
              ("max_resident",ctypes.c_uint64),("user_seconds",ctypes.c_int),
              ("user_micros",ctypes.c_int),("system_seconds",ctypes.c_int),
              ("system_micros",ctypes.c_int),("policy",ctypes.c_int),("suspend",ctypes.c_int)]


class Memory:
    """20ms sampled peaks, not an exact allocator high-water measurement."""
    def __init__(self):
        self.stop=threading.Event()
        self.peaks={"mps_allocated":0,"mps_driver_allocated":0,"process_resident":0}
        self.samples=0
        self.lib=ctypes.CDLL("/usr/lib/libSystem.B.dylib")
        self.lib.mach_task_self.restype=ctypes.c_uint32
        self.task=self.lib.mach_task_self()
    def sample(self):
        vals={"mps_allocated":torch.mps.current_allocated_memory(),
              "mps_driver_allocated":torch.mps.driver_allocated_memory()}
        info=TaskInfo();count=ctypes.c_uint32(ctypes.sizeof(info)//4)
        ret=self.lib.task_info(self.task,20,ctypes.byref(info),ctypes.byref(count))
        if ret==0:vals["process_resident"]=int(info.resident)
        for k,v in vals.items():self.peaks[k]=max(self.peaks[k],v)
        self.samples+=1
    def loop(self):
        while not self.stop.wait(.02):self.sample()
    def __enter__(self):
        self.sample();self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start();return self
    def __exit__(self,*args):
        self.stop.set();self.thread.join();self.sample()
    def result(self):return {"sampled_peak_bytes":self.peaks,"sample_count":self.samples,"sample_interval_seconds":.02,
                             "process_lifetime_max_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                             "note":"MPS allocated/driver and process resident share unified memory; do not sum. Peaks are sampled."}


def score(parsed,target):
    value=parsed.get("value")
    accepted=parsed.get("parse_status")=="accepted_terminal_answer" or parsed.get("parse_status")=="accepted_legacy_answer"
    # Legacy wrapper may use a different accepted label; a non-None value is legacy acceptance.
    if parsed.get("policy")=="legacy":accepted=value is not None
    exact=accepted and int(value)==target
    mod=accepted and int(value)%10==target%10
    return {**parsed,"exact_correct":bool(exact),"mod10_correct":bool(mod),"proxy_only_correct":bool(mod and not exact)}


def parse_scores(text,target):
    terminal=EX.extract_terminal(text)
    declared=EX.extract_terminal(text,declared_only=True)
    legacy={**EX.extract_legacy(text),"policy":"legacy"}
    return {"legacy":score(legacy,target),"terminal":score(terminal,target),"declared":score(declared,target)}


def prepare_config(model,cap):
    config=copy.deepcopy(model.generation_config)
    config.do_sample=False;config.num_beams=1;config.num_return_sequences=1
    config.max_new_tokens=cap;config.eos_token_id=list(EOS);config.pad_token_id=151643
    config.repetition_penalty=1.1
    # These sampling-only defaults are inactive; normalize to avoid misleading warnings.
    config.temperature=1.0;config.top_p=1.0;config.top_k=50
    config.return_dict_in_generate=True;config.output_scores=False
    return config


def generate(model,tokenizer,item,label,config,phase,out,adapter_hash):
    row={"schema":"arithmetic-local-pilot-1","phase":phase,"model":label,
         "problem_id":item["problem_id"],"a":item["a"],"b":item["b"],"c":item["c"],
         "ground_truth":item["result"],"max_new_tokens":config.max_new_tokens,
         "base_revision":BASE.name,"adapter_sha256":adapter_hash,"extractor_version":EX.VERSION,
         "effective_generation_config_sha256":hashlib.sha256(config.to_json_string(use_diff=False).encode()).hexdigest(),
         "precision":"float16","device":"mps","configured_eos_ids":list(EOS)}
    started=time.perf_counter()
    messages=[{"role":"system","content":"You are a helpful mathematical assistant."},
              {"role":"user","content":item["prompt"]}]
    rendered=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    inputs=tokenizer([rendered],return_tensors="pt",padding=True).to("mps")
    prompt=inputs.input_ids[0].tolist()
    row.update({"rendered_prompt":rendered,"prompt_sha256":hashlib.sha256(rendered.encode()).hexdigest(),
                "prompt_token_ids":prompt,"prompt_token_count":len(prompt)})
    torch.manual_seed(SEED);torch.mps.manual_seed(SEED);random.seed(SEED)
    try:
        torch.mps.synchronize();before=time.perf_counter()
        with torch.inference_mode():result=model.generate(**inputs,generation_config=config)
        torch.mps.synchronize();elapsed=time.perf_counter()-before
        sequence=result.sequences[0].cpu().tolist()
        assert sequence[:len(prompt)]==prompt
        ids=sequence[len(prompt):]
        meta=stopping(ids,config.max_new_tokens)
        assert meta["ids_after_first_eos"]==0
        assert meta["stopping_reason"]!="unexpected_stop"
        raw=tokenizer.decode(ids,skip_special_tokens=False)
        readable=tokenizer.decode(ids,skip_special_tokens=True)
        row.update({"generated_token_ids":ids,"raw_sequence_length":len(sequence),**meta,
                    "raw_completion":raw,"readable_completion":readable,
                    "generation_seconds":elapsed,"visible_retokenized_count":len(tokenizer.encode(readable,add_special_tokens=False)),
                    "scores":parse_scores(readable,item["result"]),"error":None})
        del result,inputs
    except Exception as exc:
        row.update({"stopping_reason":"error","error":repr(exc),"traceback":traceback.format_exc()})
        append(out/"responses.jsonl",row)
        raise
    row["record_seconds"]=time.perf_counter()-started
    append(out/"responses.jsonl",row)
    return row


def main(stage,attempt):
    started=time.perf_counter()
    freeze=json.loads((HERE/"freeze.json").read_text())
    for name,want in freeze["source_sha256"].items():
        if sha(HERE/name)!=want:raise ValueError(f"Frozen source changed: {name}")
    for path,want in freeze["model_files_sha256"].items():
        if sha(Path(path))!=want:raise ValueError(f"Frozen model bytes changed: {path}")
    if stage=="timing":
        evidence=json.loads((HERE/"attempts"/attempt/"smoke"/"validation.json").read_text())
        if not evidence["pass"]:raise ValueError("Timing requires the same attempt's passing smoke test")
    out=HERE/"attempts"/attempt/stage
    out.mkdir(parents=True,exist_ok=False)
    dump(out/"source_freeze.json",freeze)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.mps.set_per_process_memory_fraction(.8)
    torch.manual_seed(SEED);torch.mps.manual_seed(SEED);random.seed(SEED)
    assert torch.backends.mps.is_available()
    host={"platform":platform.platform(),"machine":platform.machine(),"python":platform.python_version(),
          "packages":{n:importlib.metadata.version(n) for n in ("torch","transformers","peft","tokenizers","accelerate")},
          "device":"mps","dtype":"float16","attention_implementation":"eager",
          "deterministic_algorithms":torch.are_deterministic_algorithms_enabled(),
          "deterministic_warn_only":torch.is_deterministic_algorithms_warn_only_enabled(),
          "mps_cpu_fallback_env":os.environ["PYTORCH_ENABLE_MPS_FALLBACK"],
          "memory_fraction":.8,"recommended_max_memory_bytes":torch.mps.recommended_max_memory(),
          "hardware":subprocess.check_output(["/usr/sbin/sysctl","-n","hw.model","hw.memsize","machdep.cpu.brand_string"],text=True).strip().splitlines(),
          "stage":stage,"seed":SEED,"metadata_self_test":metadata_self_test()}
    dump(out/"host.json",host)
    data=[json.loads(x) for x in (HERE/"preparation/development.jsonl").read_text().splitlines()]
    n=3 if stage=="smoke" else 20
    assert len(data)==500
    data=data[:n]
    tokenizer=AutoTokenizer.from_pretrained(BASE,local_files_only=True,trust_remote_code=False)
    if tokenizer.pad_token_id is None:tokenizer.pad_token_id=151643
    dump(out/"base_generation_config.json",json.loads((BASE/"generation_config.json").read_text()))
    cells=[];prefix_checks=[];repeats=[];config_records=[]
    try:
        for label,adapter in MODELS:
            gc.collect();torch.mps.empty_cache();torch.mps.synchronize()
            load_start=time.perf_counter()
            with Memory() as load_mem:
                model=AutoModelForCausalLM.from_pretrained(BASE,local_files_only=True,trust_remote_code=False,
                                                         dtype=torch.float16,attn_implementation="eager")
                if adapter:model=PeftModel.from_pretrained(model,adapter,is_trainable=False,autocast_adapter_dtype=False,local_files_only=True)
                model=model.to(device="mps",dtype=torch.float16)
                model.eval();torch.mps.synchronize()
            load_seconds=time.perf_counter()-load_start
            dtypes=Counter(str(p.dtype) for p in model.parameters() if p.is_floating_point())
            devices=Counter(str(p.device) for p in model.parameters())
            assert set(dtypes)=={"torch.float16"},dtypes
            assert all(d.startswith("mps") for d in devices),devices
            ah=sha(adapter/"adapter_model.safetensors") if adapter else None
            append(out/"loading.jsonl",{"model":label,"loading_seconds":load_seconds,"parameter_dtypes":dict(dtypes),
                                         "parameter_devices":dict(devices),"adapter_sha256":ah,**load_mem.result()})
            generations={}
            for cap in CAPS:
                config=prepare_config(model,cap)
                config_records.append({"model":label,"cap":cap,"configuration":config.to_dict(),
                                       "sha256":hashlib.sha256(config.to_json_string(use_diff=False).encode()).hexdigest()})
                cell_started=time.perf_counter();rows=[]
                with Memory() as mem:
                    for item in data:
                        r=generate(model,tokenizer,item,label,config,stage,out,ah)
                        rows.append(r);generations[(item["problem_id"],cap)]=r
                        if len(rows)%5==0 or stage=="smoke":
                            print(json.dumps({"stage":stage,"model":label,"cap":cap,"done":len(rows),"of":n,
                                              "seconds":round(time.perf_counter()-cell_started,2)}),flush=True)
                cell={"model":label,"cap":cap,"n":len(rows),"cell_seconds":time.perf_counter()-cell_started,
                      "generation_seconds":sum(r["generation_seconds"] for r in rows),
                      "record_seconds":sum(r["record_seconds"] for r in rows),
                      "actual_generated_tokens":sum(r["generated_token_count"] for r in rows),
                      "seconds_per_example":[r["generation_seconds"] for r in rows],
                      "stopping_counts":dict(Counter(r["stopping_reason"] for r in rows)),"errors":0,
                      **mem.result()}
                cells.append(cell);append(out/"cells.jsonl",cell)
            for item in data:
                for c1,c2 in itertools.combinations(CAPS,2):
                    a,b=generations[item["problem_id"],c1],generations[item["problem_id"],c2]
                    ids1,ids2=a["generated_token_ids"],b["generated_token_ids"]
                    prefix=ids1==ids2[:len(ids1)]
                    eos_consistency=(not a["stopping_reason"].startswith("eos")) or ids1==ids2
                    prefix_checks.append({"model":label,"problem_id":item["problem_id"],"caps":[c1,c2],
                                          "prefix_identical":prefix,"terminated_short_is_identical":eos_consistency})
            if stage=="smoke":
                # 21 extra replay calls, reported separately from the 63 unique smoke cells.
                for item in data:
                    r=generate(model,tokenizer,item,label,prepare_config(model,128),"repeat",out,ah)
                    same=r["generated_token_ids"]==generations[item["problem_id"],128]["generated_token_ids"]
                    repeats.append({"model":label,"problem_id":item["problem_id"],"cap":128,"identical":same})
                if label=="Base":
                    config=prepare_config(model,4)
                    config.min_new_tokens=3;config.forced_eos_token_id=151645
                    r=generate(model,tokenizer,data[0],label,config,"forced_eos_control",out,ah)
                    assert r["stopping_reason"]=="eos_at_limit"
            del model
            gc.collect();torch.mps.empty_cache();torch.mps.synchronize()
        validation={"pass":all(x["prefix_identical"] and x["terminated_short_is_identical"] for x in prefix_checks)
                    and all(x["identical"] for x in repeats),"planned_completions":7*3*n,
                    "prefix_comparisons":len(prefix_checks),"prefix_failures":[x for x in prefix_checks if not(x["prefix_identical"] and x["terminated_short_is_identical"])],
                    "determinism_replays":len(repeats),"replay_failures":[x for x in repeats if not x["identical"]],
                    "elapsed_seconds":time.perf_counter()-started,"cells":len(cells),"errors":0,
                    "scope":"Only this stage's fixed first3/20 examples; no full-matrix execution."}
        dump(out/"validation.json",validation)
        dump(out/"prefix_checks.json",prefix_checks);dump(out/"determinism_replays.json",repeats)
        dump(out/"generation_configs.json",config_records)
        print(json.dumps(validation),flush=True)
        if not validation["pass"]:raise RuntimeError("Prefix/determinism validation failed; preserve attempt and restart after amendment")
    except Exception as exc:
        dump(out/"failure.json",{"error":repr(exc),"traceback":traceback.format_exc(),"elapsed_seconds":time.perf_counter()-started,
                                 "completed_cells":len(cells),"restart_required":True})
        raise


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",required=True,choices=("smoke","timing"))
    parser.add_argument("--attempt",required=True)
    args=parser.parse_args()
    if not __import__("re").fullmatch(r"[a-zA-Z0-9_-]+",args.attempt):raise ValueError("Unsafe attempt name")
    main(args.stage,args.attempt)
