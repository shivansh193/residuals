# Residuals voice spikes 3 + 4, run on a Kaggle GPU.
#
# Phase A (kokoro venv): design 5 fully synthetic personas by blending Kokoro-82M
#   voice packs (no single real speaker), and render each persona's enrolment
#   passage, a short clone reference and 40 test sentences ("originals").
# Phase B (f5 venv): make a zero-shot AI clone of each persona with F5-TTS from
#   the persona's own synthetic reference, speaking the same 40 sentences.
# Phase C (base env): ECAPA speaker verification EER, and clone-vs-original
#   detection (pretrained deepfake detector, zero-shot + a wav2vec2 probe
#   evaluated leave-one-persona-out).
#
# Each phase runs in its own process so the TTS stacks can't break each other.
import json, os, subprocess, sys, textwrap

W = "/kaggle/working/out"
T = "/kaggle/tmp"
os.makedirs(W, exist_ok=True)
os.makedirs(T, exist_ok=True)

PERSONAS = [
    {"id": "mara", "name": "Mara Vell", "mix": {"af_heart": 0.6, "af_nicole": 0.4}, "speed": 1.0},
    {"id": "theo", "name": "Theo Rusk", "mix": {"am_michael": 0.5, "am_fenrir": 0.5}, "speed": 0.95},
    {"id": "juno", "name": "Juno Park", "mix": {"af_bella": 0.5, "af_sky": 0.5}, "speed": 1.05},
    {"id": "silas", "name": "Silas Orne", "mix": {"am_onyx": 0.6, "am_eric": 0.4}, "speed": 0.92},
    {"id": "ivy", "name": "Ivy Calder", "mix": {"af_sarah": 0.6, "af_jessica": 0.4}, "speed": 1.0},
]

ENROL = (
    "My name is {name}. I am recording this statement myself, today, to enrol my own voice with Residuals. "
    "I consent to my voice being matched against audio submitted to the service, and I set my own licence terms. "
    "Nobody else may enrol my voice on my behalf. "
    "The harbour was quiet that morning. A thin fog rolled in over the water, and the fishing boats waited at their moorings. "
    "Along the sea wall, a baker opened her shutters and the smell of warm bread drifted down the street. "
    "Children ran past with their school bags, and an old man fed the gulls from a paper bag. "
    "By noon the fog had lifted, the market was full of voices, and the whole town seemed to wake up at once."
)
REF_TEXT = "I am recording this short sample of my own voice so that my licensed clone can be tracked and paid fairly."

SENTENCES = [
    # ads
    "Introducing the all new Brightline blender, with twice the power and half the noise.",
    "This weekend only, every pair of running shoes is thirty percent off. Don't miss it.",
    "Fresh coffee, delivered to your door every Monday. Your first box is on us.",
    "Upgrade to Nimbus Cloud today and get unlimited storage for your whole family.",
    "Feel the difference with Harbor mattresses. Try one free for a hundred nights.",
    "Book your summer getaway now and save up to two hundred dollars on flights.",
    "Crisp, cold and refreshing. Polar Spring water, straight from the mountains.",
    "Switch your phone plan in five minutes and keep your number. It's that easy.",
    # narration / audiobook
    "Chapter three. The letter arrived on a Tuesday, folded twice and sealed with blue wax.",
    "The river had changed its course many times over the centuries, carving the valley we see today.",
    "She paused at the door, listening to the rain, and wondered whether he would come back at all.",
    "In the deep ocean, where sunlight never reaches, strange creatures make their own light.",
    "The old lighthouse keeper kept a journal, and every entry began with the weather.",
    "By the end of the war, the small village had lost half of its families to the city.",
    "Bees communicate the location of flowers to each other with a dance inside the hive.",
    "He counted the steps to the top of the tower. There were exactly two hundred and twelve.",
    # e-learning / corporate
    "Welcome to module two. In this lesson, we will cover the basics of workplace safety.",
    "Before you begin, make sure your headphones are connected and your volume is turned up.",
    "Click next to continue, or select replay to watch this section again.",
    "Quarterly revenue grew by eight percent, driven mostly by strong sales in the north region.",
    # games
    "Stay behind me. The bridge won't hold us both if we run.",
    "You found the silver key. Maybe it opens the door in the east tower.",
    "Traveller, you look tired. Sit by the fire and tell me where you have come from.",
    "Shields are down to forty percent. We need to retreat, now!",
    # non-profit / PSA
    "Every donation helps us plant trees in communities that lost their forests to wildfire.",
    "Remember to check on your elderly neighbours during the heatwave. A short visit can save a life.",
    "Our food bank is open every Saturday morning. Everyone is welcome, no questions asked.",
    "Volunteers are needed to help clean the beach this Sunday. Gloves and bags are provided.",
    # political
    "Vote for change this November. Together we can fix the roads and lower your taxes.",
    "My opponent has failed this district for ten years. It's time for new leadership.",
    "Paid for by the committee to elect a better council. Make your voice heard on election day.",
    "Support Measure Twelve and keep our schools funded for the next generation.",
    # podcast / social
    "Hey everyone, welcome back to the show. Today we're talking about the best budget cameras.",
    "Don't forget to like and subscribe, it really helps the channel grow.",
    "So I tried cooking every meal at home for a month, and here's what happened.",
    "Quick tip: if your bread is going stale, sprinkle it with water and warm it in the oven.",
    # misc / dubbing
    "I never said I would stay. I only said I would think about it.",
    "The train to the city leaves from platform four in ten minutes.",
    "Thank you for calling. Your call is important to us, please stay on the line.",
    "Tomorrow will be mostly sunny with a light breeze from the west.",
]
USE_TYPES = (["ad"] * 8 + ["narration"] * 8 + ["elearning"] * 4 + ["game"] * 4 +
             ["nonprofit"] * 4 + ["political"] * 4 + ["social"] * 4 + ["other"] * 4)
assert len(SENTENCES) == len(USE_TYPES) == 40

json.dump({"personas": PERSONAS, "enrol": ENROL, "ref_text": REF_TEXT,
           "sentences": SENTENCES, "use_types": USE_TYPES},
          open(f"{T}/spec.json", "w"), indent=1)
json.dump({"personas": PERSONAS, "ref_text": REF_TEXT, "sentences": SENTENCES,
           "use_types": USE_TYPES}, open(f"{W}/spec.json", "w"), indent=1)

PHASE_A = r'''
import json, numpy as np, soundfile as sf, torch
from kokoro import KPipeline
S = json.load(open("/kaggle/tmp/spec.json"))
W = "/kaggle/working/out"
pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
def say(text, voice, speed):
    parts = [r.audio.cpu().numpy() for r in pipe(text, voice=voice, speed=speed, split_pattern=r"\n+")]
    return np.concatenate(parts)
import os
for p in S["personas"]:
    d = f"{W}/{p['id']}"; os.makedirs(d, exist_ok=True)
    v = sum(w * pipe.load_voice(n) for n, w in p["mix"].items())
    sf.write(f"{d}/enrol.wav", say(S["enrol"].format(name=p["name"]), v, p["speed"]), 24000)
    sf.write(f"{d}/ref.wav", say(S["ref_text"], v, p["speed"]), 24000)
    for i, t in enumerate(S["sentences"]):
        sf.write(f"{d}/orig_{i:02d}.wav", say(t, v, p["speed"]), 24000)
    print("persona done", p["id"], flush=True)
'''

PHASE_B = r'''
import json, os, soundfile as sf
from f5_tts.api import F5TTS
S = json.load(open("/kaggle/tmp/spec.json"))
W = "/kaggle/working/out"
tts = F5TTS()
for p in S["personas"]:
    d = f"{W}/{p['id']}"
    for i, t in enumerate(S["sentences"]):
        wav, sr, _ = tts.infer(ref_file=f"{d}/ref.wav", ref_text=S["ref_text"], gen_text=t,
                               seed=1000 + i, show_info=lambda *a, **k: None)
        sf.write(f"{d}/clone_{i:02d}.wav", wav, sr)
    print("clones done", p["id"], flush=True)
'''

PHASE_C = r'''
import json, numpy as np, soundfile as sf, librosa, torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_curve
S = json.load(open("/kaggle/tmp/spec.json"))
W = "/kaggle/working/out"
dev = "cuda" if torch.cuda.is_available() else "cpu"
ids = [p["id"] for p in S["personas"]]
N = len(S["sentences"])
def load16(path):
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1: y = y.mean(1)
    return librosa.resample(y, orig_sr=sr, target_sr=16000)
R = {}

# ---- Spike 3: ECAPA speaker verification ----
from speechbrain.inference.speaker import EncoderClassifier
enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir="/kaggle/tmp/ecapa",
                                     run_opts={"device": dev})
def emb(y):
    with torch.no_grad():
        e = enc.encode_batch(torch.tensor(y)[None].to(dev)).squeeze().cpu().numpy()
    return e / np.linalg.norm(e)
enrol = {}
for pid in ids:
    y = load16(f"{W}/{pid}/enrol.wav")
    # enrol from 3 s windows averaged, like a production enrolment
    win = [y[s:s + 48000] for s in range(0, len(y) - 48000, 24000)]
    m = np.mean([emb(w) for w in win], 0); enrol[pid] = m / np.linalg.norm(m)
tests = []  # (persona, kind, idx, embedding)
for pid in ids:
    for i in range(N):
        for kind in ("orig", "clone"):
            tests.append((pid, kind, i, emb(load16(f"{W}/{pid}/{kind}_{i:02d}.wav"))))
def eer(scores, labels):
    fpr, tpr, thr = roc_curve(labels, scores); fnr = 1 - tpr
    k = np.nanargmin(np.abs(fnr - fpr)); return float((fpr[k] + fnr[k]) / 2), float(thr[k])
def trials(kinds):
    sc, lb = [], []
    for pid, kind, i, e in tests:
        if kind not in kinds: continue
        for q in ids:
            sc.append(float(e @ enrol[q])); lb.append(int(q == pid))
    return np.array(sc), np.array(lb)
sv = {}
for name, kinds in [("originals", ("orig",)), ("clones", ("clone",)), ("all", ("orig", "clone"))]:
    sc, lb = trials(kinds); e, th = eer(sc, lb)
    sv[name] = {"eer": e, "eer_threshold": th, "n_target": int(lb.sum()), "n_nontarget": int((1 - lb).sum()),
                "target_mean": float(sc[lb == 1].mean()), "nontarget_mean": float(sc[lb == 0].mean()),
                "nontarget_max": float(sc[lb == 0].max())}
# operating point: identification (best-matching persona must be correct AND above threshold)
th = sv["all"]["eer_threshold"]
tp = fp = fn = 0
for pid, kind, i, e in tests:
    s = {q: float(e @ enrol[q]) for q in ids}; best = max(s, key=s.get)
    if s[best] >= th:
        if best == pid: tp += 1
        else: fp += 1; fn += 1
    else: fn += 1
sv["operating_point"] = {"threshold": th, "precision": tp / max(tp + fp, 1), "recall": tp / (tp + fn)}
# persona-to-persona similarity (how close the designed voices are)
sv["enrol_similarity"] = {a: {b: round(float(enrol[a] @ enrol[b]), 3) for b in ids} for a in ids}
R["speaker_verification"] = sv
print(json.dumps(sv, indent=1), flush=True)

# ---- Spike 4: clone (F5) vs designed original (Kokoro) ----
files = [(pid, kind, i) for pid in ids for i in range(N) for kind in ("orig", "clone")]
y_true = np.array([int(k == "clone") for _, k, _ in files]); groups = np.array([p for p, _, _ in files])
cd = {}
# (a) zero-shot pretrained deepfake detector
try:
    from transformers import pipeline
    det = pipeline("audio-classification", model="MelodyMachine/Deepfake-audio-detection-V2",
                   device=0 if dev == "cuda" else -1)
    fake_p = []
    for pid, kind, i in files:
        out = det({"raw": load16(f"{W}/{pid}/{kind}_{i:02d}.wav"), "sampling_rate": 16000}, top_k=None)
        d = {o["label"].lower(): o["score"] for o in out}
        fake_p.append(d.get("fake", d.get("spoof", 1 - d.get("real", d.get("bonafide", 0.5)))))
    fake_p = np.array(fake_p)
    cd["pretrained_zero_shot"] = {"model": "MelodyMachine/Deepfake-audio-detection-V2",
        "frac_flagged_fake_originals": float((fake_p[y_true == 0] > 0.5).mean()),
        "frac_flagged_fake_clones": float((fake_p[y_true == 1] > 0.5).mean()),
        "accuracy_clone_vs_original": float(((fake_p > 0.5) == y_true).mean())}
except Exception as ex:
    cd["pretrained_zero_shot"] = {"error": repr(ex)[:300]}
print(json.dumps(cd, indent=1), flush=True)
# (b) wav2vec2 probe, leave-one-persona-out
from transformers import AutoFeatureExtractor, Wav2Vec2Model
fe = AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-base")
w2v = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base").to(dev).eval()
X = []
for pid, kind, i in files:
    y = load16(f"{W}/{pid}/{kind}_{i:02d}.wav")
    with torch.no_grad():
        h = w2v(**{k: v.to(dev) for k, v in fe(y, sampling_rate=16000, return_tensors="pt").items()},
                output_hidden_states=True).hidden_states
    X.append(np.concatenate([np.concatenate([h[L][0].mean(0).cpu().numpy(), h[L][0].std(0).cpu().numpy()])
                             for L in (3, 6, 9)]))
X = np.array(X)
pred = np.zeros_like(y_true); prob = np.zeros(len(files))
per = {}
for g in ids:
    tr, te = groups != g, groups == g
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1)).fit(X[tr], y_true[tr])
    prob[te] = clf.predict_proba(X[te])[:, 1]; pred[te] = (prob[te] > 0.5).astype(int)
    per[g] = float((pred[te] == y_true[te]).mean())
cd["w2v2_probe_lopo"] = {"accuracy": float((pred == y_true).mean()),
    "false_positive_rate_on_originals": float(pred[y_true == 0].mean()),
    "recall_on_clones": float(pred[y_true == 1].mean()), "per_heldout_persona_accuracy": per}
R["clone_detection"] = cd
R["durations_s"] = {pid: {"enrol": len(load16(f"{W}/{pid}/enrol.wav")) / 16000} for pid in ids}
json.dump(R, open(f"{W}/results.json", "w"), indent=1)
print(json.dumps(cd, indent=1), flush=True)
'''

for name, code in [("a", PHASE_A), ("b", PHASE_B), ("c", PHASE_C)]:
    open(f"{T}/phase_{name}.py", "w").write(textwrap.dedent(code))

PROG = f"{W}/progress.log"


def sh(cmd, check=True):
    """Run a step; keep its output in /kaggle/working so it survives a crashed session."""
    n = len(open(PROG).read().splitlines()) if os.path.exists(PROG) else 0
    logf = f"{W}/step_{n:02d}.log"
    with open(PROG, "a") as f:
        f.write(f"START {cmd}\n")
    print("+", cmd, flush=True)
    with open(logf, "w") as lf:
        r = subprocess.run(cmd, shell=True, stdout=lf, stderr=subprocess.STDOUT)
    tail = open(logf, errors="replace").read()[-3000:]
    print(tail, flush=True)
    with open(PROG, "a") as f:
        f.write(f"END rc={r.returncode} {cmd}\n")
    if check and r.returncode:
        raise SystemExit(f"step failed rc={r.returncode}: {cmd}")
    return r

sh("nvidia-smi --query-gpu=name,memory.total --format=csv", check=False)
sh("python -c 'import torch,torchaudio,transformers;print(torch.__version__,torchaudio.__version__,transformers.__version__)'", check=False)
sh("apt-get -qq update >/dev/null 2>&1; apt-get -qq install -y espeak-ng >/dev/null 2>&1", check=False)

sh(f"python -m venv --without-pip --system-site-packages {T}/vk && {T}/vk/bin/python -m pip install -q --no-deps --ignore-requires-python kokoro==0.9.4 misaki==0.9.4 && {T}/vk/bin/python -m pip install -q --prefer-binary num2words phonemizer-fork espeakng-loader loguru addict soundfile && ({T}/vk/bin/python -c 'import spacy' || {T}/vk/bin/python -m pip install -q --only-binary=:all: spacy) && {T}/vk/bin/python -m spacy download en_core_web_sm")
sh(f"{T}/vk/bin/python {T}/phase_a.py")

sh(f"python -m venv --without-pip --system-site-packages {T}/vf && {T}/vf/bin/python -m pip install -q --prefer-binary --ignore-requires-python f5-tts soundfile")
sh(f"{T}/vf/bin/python -m pip install -q torchcodec", check=False)
sh(f"{T}/vf/bin/python {T}/phase_b.py")

sh("pip install -q speechbrain==1.0.3")
sh(f"python {T}/phase_c.py")
print("ALL DONE", flush=True)
