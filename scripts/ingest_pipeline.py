"""Ingest the Kaggle pipeline output into fixtures/ and run the Gemini use-type step.

python scripts/ingest_pipeline.py <kaggle_output_dir>

- fixtures/audio_public/<file>.mp3     audio served to the web app
- fixtures/audio/<file_id>/truth.json  hand-checkable ground truth (built from the known composition)
- fixtures/analysis/<file_id>.json     pipeline output + Gemini use type
- fixtures/eval/*.json                 spike + pipeline + use-type evaluation
"""
import glob, json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
from server import gemini  # noqa: E402
from server.policy import USE_TYPES  # noqa: E402

SRC = sys.argv[1]
OUT = glob.glob(os.path.join(SRC, "**", "pipeline_eval.json"), recursive=True)
assert OUT, "no pipeline_eval.json under " + SRC
SRC = os.path.dirname(OUT[0])
F = os.path.join(ROOT, "fixtures")
for d in ("audio_public", "analysis", "eval"):
    os.makedirs(os.path.join(F, d), exist_ok=True)

USE_SCHEMA = {"type": "OBJECT", "properties": {
    "use_type": {"type": "STRING", "enum": USE_TYPES}, "reason": {"type": "STRING"}}, "required": ["use_type", "reason"]}
USE_PROMPT = ("Classify how this audio uses a voice. Use types: ad (advertising a product/service), narration "
              "(audiobook/documentary/story), elearning (training/corporate), game (video game dialogue), nonprofit "
              "(charity/public-service announcement), political (campaigns, elections, ballot measures, candidates), "
              "social (creator/social video/podcast), adult, other. Political wins over ad if it promotes a candidate "
              "or measure. reason: one short sentence citing the words that decided it.\nTranscript:\n\"\"\"{t}\"\"\"")

for d in sorted(glob.glob(os.path.join(SRC, "*", "analysis.json"))):
    a = json.load(open(d))
    fid = a["file_id"]
    wav = os.path.join(os.path.dirname(d), a["file_name"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "64k",
                    os.path.join(F, "audio_public", a["audio"])], check=True)
    os.makedirs(os.path.join(F, "audio", fid), exist_ok=True)
    shutil.copy(os.path.join(os.path.dirname(d), "truth.json"), os.path.join(F, "audio", fid, "truth.json"))
    r = gemini.generate_json(USE_PROMPT.format(t=a["transcript"]), USE_SCHEMA)
    a["use_type"], a["use_type_reason"] = r["use_type"], r["reason"]
    a["pipeline"]["use_type"] = "Gemini (structured output)"
    json.dump(a, open(os.path.join(F, "analysis", f"{fid}.json"), "w"), indent=1)
    print(fid, a["use_type"], "|", r["reason"])

shutil.copy(OUT[0], os.path.join(F, "eval", "pipeline_eval.json"))
sp = os.path.join(SRC, "spike_results.json")
if os.path.exists(sp):
    shutil.copy(sp, os.path.join(F, "eval", "spike_results.json"))

# Use-type accuracy on the 40 labelled sentences, one batched call
spec = json.load(open(glob.glob(os.path.join(sys.argv[1], "**", "spec.json"), recursive=True)[0])) \
    if glob.glob(os.path.join(sys.argv[1], "**", "spec.json"), recursive=True) else None
if spec is None:
    spec = json.load(open(os.path.join(ROOT, "kaggle", "spec_sentences.json")))
items = "\n".join(f"{i}. {s}" for i, s in enumerate(spec["sentences"]))
schema = {"type": "OBJECT", "properties": {"labels": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "i": {"type": "INTEGER"}, "use_type": {"type": "STRING", "enum": USE_TYPES}}, "required": ["i", "use_type"]}}},
    "required": ["labels"]}
r = gemini.generate_json("For each numbered line, classify the voice use. " + USE_PROMPT.split("Transcript:")[0] +
                         "\nLines:\n" + items, schema)
pred = {x["i"]: x["use_type"] for x in r["labels"]}
truth = spec["use_types"]
rows = [{"i": i, "text": s, "truth": truth[i], "pred": pred.get(i)} for i, s in enumerate(spec["sentences"])]
acc = sum(r_["truth"] == r_["pred"] for r_ in rows) / len(rows)
conf = {}
for r_ in rows:
    conf.setdefault(r_["truth"], {}).setdefault(r_["pred"], 0)
    conf[r_["truth"]][r_["pred"]] += 1
json.dump({"accuracy": acc, "n": len(rows), "confusion": conf, "rows": rows},
          open(os.path.join(F, "eval", "use_type_eval.json"), "w"), indent=1)
print("use-type accuracy", round(acc, 3), [r_ for r_ in rows if r_["truth"] != r_["pred"]])
