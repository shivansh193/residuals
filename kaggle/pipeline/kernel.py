# Residuals detection pipeline on demo files (Kaggle GPU).
#
# Input: the synthetic persona corpus from the voice-spikes kernel (originals, clones, enrolment audio).
# 1. Build 5 demo files from that corpus, with exact ground truth (truth.json).
# 2. Run the pipeline on each file as if it were unknown audio:
#    VAD (Silero) -> sliding-window ECAPA embeddings -> enrolled-voice diarization (assign each window to the
#    best enrolled voice above the calibrated threshold, else "unknown"; merge + smooth) -> clone detector
#    (wav2vec2 probe trained leave-one-persona-out, so it never saw the persona it scores) -> ASR (Whisper)
#    with timestamps mapped onto segments.
# 3. Score against ground truth: per-voice minutes error, segment label accuracy, clone accuracy.
# Use-type classification (Gemini) runs afterwards on the transcripts, outside Kaggle.
import glob, json, os, subprocess, sys

IN = glob.glob("/kaggle/input/**/spec.json", recursive=True)
if not IN:
    subprocess.run("find /kaggle/input -maxdepth 4 | head -50", shell=True)
assert IN, "persona dataset not mounted"
SRC = os.path.dirname(IN[0])
W = "/kaggle/working/out"
os.makedirs(W, exist_ok=True)


class _Tee:  # keep a copy of stdout/stderr in /kaggle/working so a crashed session still leaves a log
    def __init__(self, *s): self.s = s
    def write(self, x):
        for f in self.s: f.write(x); f.flush()
    def flush(self):
        for f in self.s: f.flush()

    def isatty(self):
        return False

    def __getattr__(self, name):
        return getattr(self.s[0], name)


_log = open(f"{W}/run.log", "a")
sys.stdout, sys.stderr = _Tee(sys.stdout, _log), _Tee(sys.stderr, _log)
print("source", SRC, flush=True)
subprocess.run("pip install -q silero-vad speechbrain==1.0.3", shell=True, check=True)

import numpy as np, soundfile as sf, librosa, torch
import torchaudio
if not hasattr(torchaudio, "list_audio_backends"):  # torchaudio 2.9+ removed it; speechbrain 1.0.3 still calls it
    torchaudio.list_audio_backends = lambda: ["soundfile"]
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve

SPEC = json.load(open(f"{SRC}/spec.json"))
SR = 16000
dev = "cuda" if torch.cuda.is_available() else "cpu"
rng = np.random.default_rng(7)
ids = [p["id"] for p in SPEC["personas"]]


def load(path):
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(1)
    y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    return y / (np.abs(y).max() + 1e-9) * 0.7


# ---------- 1. demo files ----------
# (voice, kind, sentence index). Sentence index -> use type is in SPEC["use_types"].
DEMOS = [
    ("brightline_ad", "Brightline spring campaign (radio ad)", "brightline_spring_ad.wav",
     "A 60-second radio spot. Brightline licenses Mara Vell and Ivy Calder.",
     [("mara", "clone", i) for i in (0, 4, 5, 2, 7, 3)] + [("ivy", "orig", 6), ("mara", "clone", 1)]),
    ("northpeak_trailer", "Northpeak 'Ashfall' game trailer", "northpeak_ashfall_trailer.wav",
     "Game trailer dialogue. Northpeak licenses Theo Rusk, but not Silas Orne.",
     [("theo", "clone", 20), ("silas", "clone", 23), ("theo", "clone", 22), ("silas", "orig", 21),
      ("theo", "clone", 15)]),
    ("quickclips_compilation", "QuickClips 'Life hacks' compilation", "quickclips_life_hacks.wav",
     "A social video built from cloned voices, with no licences at all.",
     [("juno", "clone", 32), ("juno", "clone", 34), ("mara", "clone", 35), ("juno", "clone", 33)]),
    ("measure12_ad", "Measure 12 campaign spot", "measure12_campaign_spot.wav",
     "A political ad using clones of voices whose owners block political use.",
     [("silas", "clone", 28), ("silas", "clone", 31), ("mara", "clone", 29), ("silas", "clone", 30)]),
    ("foodbank_psa", "Harbor Food Bank PSA", "harbor_food_bank_psa.wav",
     "A non-profit announcement. Mara and Juno let non-profits use their voices for free.",
     [("mara", "orig", 26), ("juno", "clone", 24), ("mara", "orig", 27), ("juno", "clone", 25)]),
]

files = []
for fid, title, fname, desc, parts in DEMOS:
    y, truth, t = [np.zeros(int(0.6 * SR), np.float32)], [], 0.6
    for v, kind, i in parts:
        clip = load(f"{SRC}/{v}/{kind}_{i:02d}.wav")
        clip, _ = librosa.effects.trim(clip, top_db=35)
        truth.append({"start": round(t, 3), "end": round(t + len(clip) / SR, 3), "voice_id": v,
                      "is_clone": kind == "clone", "sentence": i, "text": SPEC["sentences"][i]})
        y.append(clip)
        gap = float(rng.uniform(0.35, 0.8))
        y.append(np.zeros(int(gap * SR), np.float32))
        t += len(clip) / SR + gap
    y = np.concatenate(y)
    noise = rng.normal(0, 1, len(y)).astype(np.float32) * (np.sqrt(np.mean(y ** 2)) / 10 ** (30 / 20))
    y = (y + noise).astype(np.float32)
    os.makedirs(f"{W}/{fid}", exist_ok=True)
    sf.write(f"{W}/{fid}/{fname}", y, SR)
    json.dump({"file_id": fid, "duration_s": round(len(y) / SR, 3), "segments": truth},
              open(f"{W}/{fid}/truth.json", "w"), indent=1)
    files.append((fid, title, fname, desc, y, truth))
    print("built", fid, round(len(y) / SR, 1), "s", flush=True)

# ---------- 2a. enrolment + calibration ----------
from speechbrain.inference.speaker import EncoderClassifier
import huggingface_hub as _hh
_orig_dl = _hh.hf_hub_download


def _dl(*a, **k):  # speechbrain 1.0.3 still passes use_auth_token, which new huggingface_hub rejects
    k.pop("use_auth_token", None)
    return _orig_dl(*a, **k)


_hh.hf_hub_download = _dl
ECAPA = _hh.snapshot_download("speechbrain/spkrec-ecapa-voxceleb", local_dir="/kaggle/tmp/ecapa_src")
enc = EncoderClassifier.from_hparams(source=ECAPA, savedir="/kaggle/tmp/ecapa", run_opts={"device": dev})


def emb_batch(chunks):
    L = max(len(c) for c in chunks)
    x = torch.zeros(len(chunks), L)
    lens = torch.zeros(len(chunks))
    for i, c in enumerate(chunks):
        x[i, :len(c)] = torch.tensor(c)
        lens[i] = len(c) / L
    with torch.no_grad():
        e = enc.encode_batch(x.to(dev), lens.to(dev)).squeeze(1).cpu().numpy()
    return e / np.linalg.norm(e, axis=1, keepdims=True)


enrol = {}
for pid in ids:
    y = load(f"{SRC}/{pid}/enrol.wav")
    wins = [y[s:s + 3 * SR] for s in range(0, len(y) - 3 * SR, int(1.5 * SR))]
    m = emb_batch(wins).mean(0)
    enrol[pid] = m / np.linalg.norm(m)
E = np.stack([enrol[p] for p in ids])

# Window-level threshold calibrated on the corpus (1.5 s windows, like the pipeline uses)
WIN, HOP = int(1.5 * SR), int(0.5 * SR)
cal_s, cal_l = [], []
for pid in ids:
    for i in range(0, 40, 3):
        for kind in ("orig", "clone"):
            y = load(f"{SRC}/{pid}/{kind}_{i:02d}.wav")
            ws = [y[s:s + WIN] for s in range(0, max(1, len(y) - WIN), HOP)]
            for e in emb_batch(ws):
                sc = E @ e
                for j, q in enumerate(ids):
                    cal_s.append(sc[j]); cal_l.append(int(q == pid))
from sklearn.metrics import roc_curve
fpr, tpr, thr = roc_curve(cal_l, cal_s)
k = np.nanargmin(np.abs((1 - tpr) - fpr))
TH, WIN_EER = float(thr[k]), float((fpr[k] + 1 - tpr[k]) / 2)
print("window threshold", TH, "window EER", WIN_EER, flush=True)

# ---------- 2b. clone probe (leave-one-persona-out) ----------
from transformers import AutoFeatureExtractor, Wav2Vec2Model
fe = AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-base")
w2v = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base").to(dev).eval()


def w2v_feat(y):
    with torch.no_grad():
        h = w2v(**{k: v.to(dev) for k, v in fe(y, sampling_rate=SR, return_tensors="pt").items()},
                output_hidden_states=True).hidden_states
    return np.concatenate([np.concatenate([h[L][0].mean(0).cpu().numpy(), h[L][0].std(0).cpu().numpy()])
                           for L in (3, 6, 9)])


X, Y, G = [], [], []
for pid in ids:
    for i in range(40):
        for kind in ("orig", "clone"):
            X.append(w2v_feat(load(f"{SRC}/{pid}/{kind}_{i:02d}.wav"))); Y.append(int(kind == "clone")); G.append(pid)
X, Y, G = np.array(X), np.array(Y), np.array(G)
probes = {p: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1)).fit(X[G != p], Y[G != p])
          for p in ids}
generic = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1)).fit(X, Y)

# ---------- spikes 3 + 4 on whole utterances ----------
spikes = {}
utt = {}
for pid in ids:
    for i in range(40):
        for kind in ("orig", "clone"):
            utt[(pid, kind, i)] = emb_batch([load(f"{SRC}/{pid}/{kind}_{i:02d}.wav")])[0]


def eer_of(kinds):
    sc, lb = [], []
    for (pid, kind, i), e in utt.items():
        if kind in kinds:
            for j, q in enumerate(ids):
                sc.append(float(E[j] @ e)); lb.append(int(q == pid))
    sc, lb = np.array(sc), np.array(lb)
    f, t, th = roc_curve(lb, sc)
    k = np.nanargmin(np.abs((1 - t) - f))
    return {"eer": round(float((f[k] + 1 - t[k]) / 2), 4), "threshold": round(float(th[k]), 4),
            "n_target": int(lb.sum()), "n_nontarget": int((1 - lb).sum()),
            "target_mean": round(float(sc[lb == 1].mean()), 3), "nontarget_mean": round(float(sc[lb == 0].mean()), 3),
            "nontarget_max": round(float(sc[lb == 0].max()), 3), "target_min": round(float(sc[lb == 1].min()), 3)}


sv = {k: eer_of(v) for k, v in [("originals", ("orig",)), ("clones", ("clone",)), ("all", ("orig", "clone"))]}
th_all = sv["all"]["threshold"]
tp = fp = fn = 0
for (pid, kind, i), e in utt.items():
    sc = E @ e
    j = int(sc.argmax())
    if sc[j] >= th_all and ids[j] == pid:
        tp += 1
    elif sc[j] >= th_all:
        fp += 1; fn += 1
    else:
        fn += 1
sv["operating_point"] = {"threshold": th_all, "precision": round(tp / max(tp + fp, 1), 4), "recall": round(tp / (tp + fn), 4)}
sv["enrol_similarity"] = {a: {b: round(float(enrol[a] @ enrol[b]), 3) for b in ids} for a in ids}
spikes["speaker_verification"] = sv
pred = np.zeros_like(Y)
per = {}
for p in ids:
    m = G == p
    pred[m] = probes[p].predict(X[m])
    per[p] = round(float((pred[m] == Y[m]).mean()), 4)
spikes["clone_detection_w2v2_probe_lopo"] = {
    "accuracy": round(float((pred == Y).mean()), 4),
    "false_positive_rate_on_originals": round(float(pred[Y == 0].mean()), 4),
    "recall_on_clones": round(float(pred[Y == 1].mean()), 4), "per_heldout_persona_accuracy": per,
    "n": int(len(Y))}
try:
    from transformers import pipeline as _p
    det = _p("audio-classification", model="MelodyMachine/Deepfake-audio-detection-V2", device=0 if dev == "cuda" else -1)
    fake = []
    for pid in ids:
        for i in range(40):
            for kind in ("orig", "clone"):
                o = det({"raw": load(f"{SRC}/{pid}/{kind}_{i:02d}.wav"), "sampling_rate": SR}, top_k=None)
                d = {x["label"].lower(): x["score"] for x in o}
                fake.append((kind, d.get("fake", 1 - d.get("real", 0.5))))
    spikes["clone_detection_pretrained_zero_shot"] = {
        "model": "MelodyMachine/Deepfake-audio-detection-V2",
        "labels_seen": sorted(d.keys()),
        "flagged_fake_originals": round(float(np.mean([f > 0.5 for k, f in fake if k == "orig"])), 4),
        "flagged_fake_clones": round(float(np.mean([f > 0.5 for k, f in fake if k == "clone"])), 4)}
except Exception as ex:
    spikes["clone_detection_pretrained_zero_shot"] = {"error": repr(ex)[:300]}
json.dump(spikes, open(f"{W}/spike_results.json", "w"), indent=1)
print("SPIKES", json.dumps(spikes), flush=True)

# ---------- 2c. ASR ----------
from transformers import pipeline as hf_pipeline
asr = hf_pipeline("automatic-speech-recognition", model="openai/whisper-small", device=0 if dev == "cuda" else -1)

from silero_vad import load_silero_vad, get_speech_timestamps
vad = load_silero_vad()

# ---------- 2d. run pipeline ----------
report = {"window_threshold": TH, "window_eer": WIN_EER, "files": {}}
for fid, title, fname, desc, y, truth in files:
    speech = get_speech_timestamps(torch.tensor(y), vad, sampling_rate=SR, min_silence_duration_ms=250)
    wins = []
    for sp in speech:
        s, e = sp["start"], sp["end"]
        if e - s < int(0.4 * SR):
            continue
        starts = list(range(s, max(s + 1, e - WIN), HOP)) or [s]
        for a in starts:
            wins.append((a, min(a + WIN, e)))
    embs = emb_batch([y[a:b] for a, b in wins])
    labels, scores = [], []
    for e in embs:
        sc = E @ e
        j = int(sc.argmax())
        labels.append(ids[j] if sc[j] >= TH else None); scores.append(float(sc[j]))
    # frame-level vote at 10 ms within speech regions, then median smoothing
    n = len(y) // 160
    votes = {}
    for (a, b), lab, sc in zip(wins, labels, scores):
        for f in range(a // 160, b // 160):
            votes.setdefault(f, []).append((lab, sc))
    frame = [None] * n
    fscore = [0.0] * n
    for f, vs in votes.items():
        tally = {}
        for lab, sc in vs:
            tally[lab] = tally.get(lab, 0) + sc
        best = max(tally, key=tally.get)
        frame[f] = best if best is not None else "unknown"
        fscore[f] = float(np.mean([sc for lab, sc in vs if lab == best]))
    segs, cur = [], None
    for f in range(n):
        lab = frame[f]
        if lab is None:  # silence: keep the open segment, the gap rule below decides whether to bridge
            continue
        if cur and lab == cur["label"] and f - cur["end_f"] <= 25:
            cur["end_f"] = f; cur["sc"].append(fscore[f])
        else:
            if cur: segs.append(cur)
            cur = {"label": lab, "start_f": f, "end_f": f, "sc": [fscore[f]]}
    if cur: segs.append(cur)
    segs = [s for s in segs if (s["end_f"] - s["start_f"]) >= 40]  # drop < 0.4 s
    out = []
    for s in segs:
        a, b = s["start_f"] * 160, (s["end_f"] + 1) * 160
        vid = None if s["label"] == "unknown" else s["label"]
        feat = w2v_feat(y[a:b])
        cp = float((probes[vid] if vid else generic).predict_proba(feat[None])[0, 1])
        out.append({"start": round(a / SR, 2), "end": round(b / SR, 2), "voice_id": vid,
                    "score": round(float(np.mean(s["sc"])), 4), "clone_prob": round(cp, 3)})
    # ASR with timestamps, attach text to segments
    r = asr({"raw": y, "sampling_rate": SR}, return_timestamps=True, generate_kwargs={"language": "en"},
            chunk_length_s=30)
    chunks = r.get("chunks", [])
    for s in out:
        s["text"] = " ".join(c["text"].strip() for c in chunks
                             if c["timestamp"][0] is not None and
                             min(s["end"], c["timestamp"][1] or s["end"]) - max(s["start"], c["timestamp"][0]) > 0.3)
    analysis = {"file_id": fid, "file_name": fname, "title": title, "description": desc,
                "audio": fname.replace(".wav", ".mp3"), "duration_s": round(len(y) / SR, 2),
                "eer_threshold": TH, "transcript": r["text"].strip(), "segments": out,
                "pipeline": {"vad": "silero-vad", "diarization": "enrolled-voice sliding-window ECAPA (1.5 s/0.5 s)",
                             "embedding": "speechbrain/spkrec-ecapa-voxceleb",
                             "clone_detector": "wav2vec2-base probe, leave-one-persona-out",
                             "asr": "openai/whisper-small"}}
    json.dump(analysis, open(f"{W}/{fid}/analysis.json", "w"), indent=1)

    # ---------- 3. score against truth ----------
    def frames(segs_, key):
        arr = np.array(["-"] * n, dtype=object)
        for s in segs_:
            arr[int(s["start"] * 100):int(s["end"] * 100)] = s[key] if s[key] else "unknown"
        return arr
    tf, pf = frames(truth, "voice_id"), frames(out, "voice_id")
    speech_f = tf != "-"
    per_voice = {}
    for v in set(s["voice_id"] for s in truth):
        t_sec = sum(s["end"] - s["start"] for s in truth if s["voice_id"] == v)
        p_sec = sum(s["end"] - s["start"] for s in out if s["voice_id"] == v)
        per_voice[v] = {"truth_s": round(t_sec, 2), "pred_s": round(p_sec, 2), "abs_err_s": round(abs(p_sec - t_sec), 2)}
    clone_ok = []
    for s in out:
        if not s["voice_id"]:
            continue
        mid = (s["start"] + s["end"]) / 2
        tt = [t for t in truth if t["start"] <= mid <= t["end"]]
        if tt:
            clone_ok.append(int((s["clone_prob"] >= 0.5) == tt[0]["is_clone"]))
    report["files"][fid] = {
        "frame_label_accuracy_in_speech": round(float((tf[speech_f] == pf[speech_f]).mean()), 4),
        "per_voice_minutes": per_voice, "segments_pred": len(out), "segments_truth": len(truth),
        "clone_label_accuracy": round(float(np.mean(clone_ok)), 3) if clone_ok else None,
        "false_voice_frames": int(((pf != "-") & (pf != "unknown") & (pf != tf)).sum())}
    print(fid, json.dumps(report["files"][fid]), flush=True)

json.dump(report, open(f"{W}/pipeline_eval.json", "w"), indent=1)
print("ALL DONE", flush=True)
