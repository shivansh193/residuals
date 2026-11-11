# Residuals demo video: transcode recordings -> Hyperframes render -> Kokoro voiceover -> mix -> subtitles.
# Kaggle CPU kernel with internet. Inputs: the residuals-demo-assets dataset (webm recordings, marks.json,
# narration.json, build.py). Everything lands in /kaggle/working/out.
import glob, json, os, re, shutil, subprocess, sys

W = "/kaggle/working/out"
T = "/kaggle/tmp"
os.makedirs(W, exist_ok=True); os.makedirs(T, exist_ok=True)


class _Tee:
    def __init__(self, *s): self.s = s
    def write(self, x):
        for f in self.s: f.write(x); f.flush()
    def flush(self):
        for f in self.s: f.flush()
    def isatty(self): return False
    def __getattr__(self, n): return getattr(self.s[0], n)


_log = open(f"{W}/run.log", "a")
sys.stdout, sys.stderr = _Tee(sys.stdout, _log), _Tee(sys.stderr, _log)


def sh(cmd, check=True, cwd=None, env=None):
    print("+", cmd, flush=True)
    r = subprocess.run(cmd, shell=True, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(r.stdout[-4000:], flush=True)
    if check and r.returncode:
        raise SystemExit(f"FAILED rc={r.returncode}: {cmd}")
    return r


DATA = os.path.dirname(glob.glob("/kaggle/input/**/marks.json", recursive=True)[0])
print("data", DATA, os.listdir(DATA), flush=True)
COMP = f"{T}/comp"
os.makedirs(f"{COMP}/clips", exist_ok=True); os.makedirs(f"{COMP}/fonts", exist_ok=True)

# ---------- 1. tools ----------
sh("which ffmpeg || (apt-get -qq update && apt-get -qq install -y ffmpeg)", check=False)
sh(f"cd {T} && curl -sL https://nodejs.org/dist/v22.11.0/node-v22.11.0-linux-x64.tar.xz | tar -xJ && ls {T}")
NODE = f"{T}/node-v22.11.0-linux-x64/bin"
ENV = dict(os.environ, PATH=NODE + ":" + os.environ["PATH"])
for lib in ["libnss3", "libatk1.0-0", "libatk1.0-0t64", "libatk-bridge2.0-0", "libatk-bridge2.0-0t64", "libcups2",
            "libcups2t64", "libdrm2", "libxkbcommon0", "libxcomposite1", "libxdamage1", "libxfixes3", "libxrandr2",
            "libgbm1", "libpango-1.0-0", "libcairo2", "libasound2", "libasound2t64", "fonts-liberation", "espeak-ng"]:
    sh(f"apt-get -qq install -y {lib} >/dev/null 2>&1 && echo ok {lib} || echo skip {lib}", check=False)

# ---------- 2. clips + assets ----------
for f in glob.glob(f"{DATA}/*.webm"):
    name = os.path.basename(f)[:-5]
    sh(f"ffmpeg -y -loglevel error -i {f} -c:v libx264 -crf 21 -g 30 -pix_fmt yuv420p -r 30 -an -movflags +faststart {COMP}/clips/{name}.mp4")
for url, dst in [("https://cdn.jsdelivr.net/npm/geist@1.3.1/dist/fonts/geist-sans/Geist-Regular.woff2", "fonts/Geist-Regular.woff2"),
                 ("https://cdn.jsdelivr.net/npm/geist@1.3.1/dist/fonts/geist-sans/Geist-SemiBold.woff2", "fonts/Geist-SemiBold.woff2"),
                 ("https://cdn.jsdelivr.net/npm/geist@1.3.1/dist/fonts/geist-mono/GeistMono-Regular.woff2", "fonts/GeistMono-Regular.woff2"),
                 ("https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js", "gsap.min.js")]:
    sh(f"curl -sfL {url} -o {COMP}/{dst} && ls -la {COMP}/{dst}")
sh(f"python {DATA}/build.py {DATA} {COMP}")
TL = json.load(open(f"{COMP}/timeline.json"))
TOTAL = TL["total"]
shutil.copy(f"{COMP}/index.html", f"{W}/index.html"); shutil.copy(f"{COMP}/timeline.json", f"{W}/timeline.json")

# ---------- 3. TTS (Kokoro, Python 3.12 venv) ----------
TTS = r'''
import json, sys, soundfile as sf, numpy as np
from kokoro import KPipeline
N = json.load(open(sys.argv[1])); out = sys.argv[2]
pipe = KPipeline(lang_code="b" if N["voice"].startswith("b") else "a")
for i, l in enumerate(N["lines"]):
    a = np.concatenate([r.audio.cpu().numpy() for r in pipe(l["spoken"], voice=N["voice"], speed=1.0)])
    sf.write(f"{out}/line_{i:02d}.wav", a, 24000)
    print(i, l["section"], round(len(a) / 24000, 2), flush=True)
'''
open(f"{T}/tts.py", "w").write(TTS)
os.makedirs(f"{T}/vo", exist_ok=True)
sh("pip install -q uv")
sh(f"uv venv -p 3.12 {T}/tts")
sh(f'uv pip install --python {T}/tts/bin/python "kokoro>=0.9.4" soundfile "numpy<2.3" '
   f'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl')
sh(f"{T}/tts/bin/python {T}/tts.py {DATA}/narration.json {T}/vo")

# ---------- 4. fit voice lines ----------
import numpy as np, soundfile as sf
N = json.load(open(f"{DATA}/narration.json"))
starts = {s["section"]: s["start"] for s in TL["sections"]}
lines = N["lines"]
fit, placed = [], []
for i, l in enumerate(lines):
    st = starts[l["section"]] + 0.3
    nxt = (starts[lines[i + 1]["section"]] + 0.3) if i + 1 < len(lines) else TOTAL - 0.3
    room = nxt - st - 0.15
    y, sr = sf.read(f"{T}/vo/line_{i:02d}.wav")
    L = len(y) / sr
    tempo = 1.0 if L <= room else min(1.18, L / room)
    src = f"{T}/vo/line_{i:02d}.wav"
    if tempo > 1.0:
        sh(f"ffmpeg -y -loglevel error -i {src} -filter:a atempo={tempo:.3f} {T}/vo/fit_{i:02d}.wav")
        src = f"{T}/vo/fit_{i:02d}.wav"
    y, sr = sf.read(src)
    L2 = len(y) / sr
    fit.append({"section": l["section"], "start": round(st, 2), "length": round(L, 2), "room": round(room, 2),
                "tempo": round(tempo, 3), "final_length": round(L2, 2), "fits": L2 <= room + 0.05})
    placed.append((st, y, sr, l["written"]))
json.dump(fit, open(f"{W}/voice_fit.json", "w"), indent=1)
for f_ in fit:
    print(f_, flush=True)
sr = placed[0][2]
track = np.zeros(int((TOTAL + 1) * sr))
for st, y, _, _ in placed:
    a = int(st * sr); track[a:a + len(y)] += y[: len(track) - a]
sf.write(f"{T}/voice.wav", track, sr)

# ---------- 5. subtitles ----------
def chunks(text, maxc=84):
    out, cur = [], ""
    for piece in re.split(r"(?<=[.,:?!])\s+", text):
        if cur and len(cur) + 1 + len(piece) > maxc:
            out.append(cur); cur = piece
        else:
            cur = (cur + " " + piece).strip()
    if cur:
        out.append(cur)
    return out


def wrap(c, w=42):
    if len(c) <= w:
        return c
    cut = c.rfind(" ", 0, w + 1) if c.rfind(" ", 0, w + 1) > 0 else w
    return c[:cut] + "\n" + c[cut:].strip()


def ts(x):
    h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


cues = []
for st, y, sr_, text in placed:
    dur = len(y) / sr_
    cs = chunks(text)
    total_c = sum(len(c) for c in cs)
    t0 = st
    for c in cs:
        d = dur * len(c) / total_c
        cues.append([t0, t0 + d, wrap(c)]); t0 += d
for a, b in zip(cues, cues[1:]):
    a[1] = min(a[1], b[0] - 0.04)
open(f"{W}/residuals_demo.srt", "w").write("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues)))

# ---------- 6. music bed (generated here; no third-party music) ----------
chord = "+".join(f"{amp}*sin(2*PI*{f}*t)*(0.6+0.4*sin(2*PI*{lfo}*t))"
                 for f, amp, lfo in [(110, 0.10, 0.07), (164.81, 0.07, 0.11), (220, 0.06, 0.05), (261.63, 0.05, 0.13), (329.63, 0.04, 0.09)])
sh(f"ffmpeg -y -loglevel error -f lavfi -i \"aevalsrc='{chord}':s=48000:d={TOTAL + 1}\" "
   f"-af \"lowpass=f=1800,aecho=0.8:0.7:120|240:0.3|0.2,volume=1.6\" -ac 2 {T}/music.wav")

# ---------- 7. render ----------
sh("npx -y hyperframes@latest --help", check=False, env=ENV)
sh("npx -y hyperframes@latest browser ensure", env=ENV)
sh("npx -y hyperframes@latest render --help", check=False, env=ENV)
sh("npx -y hyperframes@latest lint", check=False, cwd=COMP, env=ENV)
sh("npx -y hyperframes@latest check", check=False, cwd=COMP, env=ENV)
sh("npx -y hyperframes@latest render --quality high", cwd=COMP, env=ENV)
mp4s = sorted(glob.glob(f"{COMP}/**/*.mp4", recursive=True), key=os.path.getmtime)
mp4s = [m for m in mp4s if "/clips/" not in m]
assert mp4s, "no render output found"
RAW = mp4s[-1]
print("render output", RAW, flush=True)
sh(f"ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of json {RAW}")

# ---------- 8. poster frame (pre-clearance result) ----------
pt = starts["preclear"] + 1.5 + 14.0
sh(f"ffmpeg -y -loglevel error -ss {pt:.2f} -i {RAW} -frames:v 1 {W}/poster.png")
sh(f"ffmpeg -y -loglevel error -i {RAW} -i {W}/poster.png -filter_complex \"[0:v][1:v]overlay=enable='eq(n,0)'\" "
   f"-c:v libx264 -crf 18 -pix_fmt yuv420p -an -movflags +faststart {T}/video.mp4")

# ---------- 9. mix ----------
fo = TOTAL - 3
sh(f"ffmpeg -y -loglevel error -i {T}/video.mp4 -i {T}/voice.wav -i {T}/music.wav -filter_complex "
   f"\"[2:a]volume=0.16,afade=t=in:d=2,afade=t=out:st={fo:.2f}:d=3[m];[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[v1][v2];"
   f"[m][v2]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=350[md];"
   f"[md][v1]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]\" "
   f"-map 0:v -map \"[a]\" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart {W}/residuals_demo.mp4")
sh(f"ffmpeg -y -loglevel error -i {T}/video.mp4 -i {T}/music.wav -filter_complex "
   f"\"[1:a]volume=0.3,afade=t=in:d=2,afade=t=out:st={fo:.2f}:d=3,loudnorm=I=-16:TP=-1.5:LRA=11[a]\" "
   f"-map 0:v -map \"[a]\" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart {W}/residuals_demo_music_only.mp4")
for f in ("residuals_demo.mp4", "residuals_demo_music_only.mp4"):
    sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {W}/{f}")
    sh(f"ffmpeg -i {W}/{f} -af volumedetect -vn -f null - 2>&1 | grep -E 'mean_volume|max_volume'", check=False)

# ---------- 10. preview sheet ----------
sh(f"ffmpeg -y -loglevel error -i {W}/residuals_demo.mp4 -vf \"fps=20/{TOTAL:.2f},scale=384:-1,tile=5x4\" -frames:v 1 {W}/preview.jpg")
print("ALL DONE", flush=True)
