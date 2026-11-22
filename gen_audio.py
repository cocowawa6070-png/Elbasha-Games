import numpy as np, subprocess
from pathlib import Path
from scipy.io import wavfile
SR = 22050
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "src" / "main" / "res" / "raw"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)

def env(n, a=0.005, d=0.1, s=0.0, r=0.0):
    t = np.arange(n)/SR
    e = np.exp(-t/max(d,1e-3))
    e[: int(a*SR)] *= np.linspace(0,1,int(a*SR))
    return e

def pluck(freq, dur, bright=0.5):
    # Karplus-Strong plucked string (oud-like)
    n = int(SR*dur)
    N = int(SR/freq)
    buf = rng.uniform(-1,1,N)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % N]
        buf[i % N] = (buf[i % N] + buf[(i+1) % N]) * 0.5 * (0.996 - 0.01*(1-bright))
    return out * np.linspace(1, 0.2, n)

def drum(kind, dur=0.35):
    n = int(SR*dur); t = np.arange(n)/SR
    if kind == "dum":   # low
        f = 95*np.exp(-t*9)+55
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*11)
    if kind == "tak":   # high rim
        noise = rng.uniform(-1,1,n)*np.exp(-t*55)
        return (noise*0.6 + np.sin(2*np.pi*1800*t)*np.exp(-t*60)*0.4)*0.7
    if kind == "sak":
        return rng.uniform(-1,1,n)*np.exp(-t*90)*0.35
    return np.zeros(n)

def place(track, sig, start):
    i = int(start*SR); j = min(len(track), i+len(sig))
    if i < len(track): track[i:j] += sig[:j-i]

def norm(x, peak=0.85):
    return (x/ (np.max(np.abs(x))+1e-9) * peak)

def save(name, x, ogg=True):
    x = norm(x)
    wav = f"/tmp/{name}.wav"
    wavfile.write(wav, SR, (x*32767).astype(np.int16))
    if ogg:
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",wav,"-c:a","libvorbis","-q:a","3",str(OUT / f"{name}.ogg")], check=True)
    print(name, round(len(x)/SR,1), "s")

# Hijaz on D: D Eb F# G A Bb C D  (oriental colour)
def hz(semi_from_d3): return 146.83 * 2**(semi_from_d3/12)
HIJAZ = [0,1,4,5,7,8,10,12]

def music_menu(bars=8, bpm=104, epic=False):
    beat = 60/bpm; bar = 4*beat; total = bars*bar
    tr = np.zeros(int(total*SR)+SR)
    # maqsum rhythm per bar (8 eighths): D T . T D . T .
    pat = ["dum","tak",None,"tak","dum",None,"tak",None]
    for b in range(bars):
        for k,p in enumerate(pat):
            if p: place(tr, drum(p)*(0.9 if p=="dum" else 0.6), b*bar + k*beat/2)
        if epic and b%2==0:
            place(tr, drum("dum",0.5)*1.1, b*bar)
            place(tr, drum("dum",0.5)*1.0, b*bar+beat*1.5)
        for k in range(8): place(tr, drum("sak")*0.25, b*bar + k*beat/2 + beat/4)
    # drone (strings pad) on D + A
    t = np.arange(len(tr))/SR
    pad = (np.sin(2*np.pi*hz(-12)*t)+0.6*np.sin(2*np.pi*hz(-5)*t)+0.3*np.sin(2*np.pi*hz(0)*t))
    pad *= 0.12*(0.7+0.3*np.sin(2*np.pi*t/(bar*2)))
    tr += pad
    # melody (oud) - phrase in Hijaz, repeated with variation
    phrase = [(7,1),(8,.5),(7,.5),(5,1),(4,1),(5,.5),(4,.5),(1,1),(0,1.5),(1,.5),
              (4,1),(5,1),(7,1),(8,1),(10,.5),(8,.5),(7,1),(5,.5),(4,.5),(1,1),(0,2)]
    pos = 0.0
    for rep in range(2 if bars>=8 else 1):
        for semi,dur in phrase:
            if pos >= total-0.5: break
            place(tr, pluck(hz(semi), dur*beat+0.4, 0.7)*0.55, pos)
            if epic: place(tr, pluck(hz(semi-12), dur*beat+0.4, 0.4)*0.35, pos)
            pos += dur*beat
    # soft electronic pulse
    for b in range(bars):
        for k in range(8):
            f = hz([0,0,7,0,5,0,4,1][k]-12)
            tt = np.arange(int(beat/2*SR))/SR
            place(tr, 0.10*np.sign(np.sin(2*np.pi*f*tt))*np.exp(-tt*8)*(1 if k%2==0 else .6), b*bar+k*beat/2)
    tr = tr[:int(total*SR)]
    # fade loop edges
    f = int(0.02*SR); tr[:f]*=np.linspace(0,1,f); tr[-f:]*=np.linspace(1,0,f)
    return tr

def tone(freqs, dur, kind="sine", decay=6):
    n=int(SR*dur); t=np.arange(n)/SR; x=np.zeros(n)
    for f in freqs:
        x += (np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t))*np.exp(-t*decay)
    return x

def seq(notes, gap=0.11, dur=0.3, decay=7):
    tr=np.zeros(int((gap*len(notes)+dur+0.2)*SR))
    for i,fs in enumerate(notes):
        place(tr, tone(fs if isinstance(fs,list) else [fs], dur, decay=decay), i*gap)
    return tr

def generate_gameplay_effects():
    """Generate the short feedback sounds used by gameplay screens."""
    save("sfx_correct", seq([hz(7), hz(11), hz(14)], 0.09, 0.35))
    t = np.arange(int(.45*SR))/SR
    wrong = np.sin(2*np.pi*(180*np.exp(-t*2.5)+90)*t)*np.exp(-t*5)
    wrong += 0.5*np.sin(2*np.pi*95*t)*np.exp(-t*4)
    save("sfx_wrong", wrong)
    save("sfx_tick", tone([1200], 0.06, decay=60))
    save("sfx_click", tone([660, 990], 0.08, decay=40))


def generate_full_audio_pack():
    # Optional standalone menu/tournament loops. They are not auto-played by the app.
    save("music_menu", music_menu(8, 104, False))
    save("music_tournament", music_menu(8, 128, True))
    generate_gameplay_effects()
    win = seq([hz(0), hz(4), hz(7), hz(12), hz(7), hz(12), hz(16), [hz(12), hz(16), hz(19)]], 0.13, 0.6, 3.5)
    dr = np.zeros(len(win))
    for k in range(6):
        place(dr, drum("dum"), k*0.11)
    place(dr, drum("dum", .6)*1.2, 0.8)
    save("sfx_win", win + 0.5*dr[:len(win)] if len(dr) >= len(win) else win)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate ELBASHA GAMES audio assets")
    parser.add_argument("--effects-only", action="store_true", help="Generate gameplay feedback only; keep existing music and win/loss assets")
    args = parser.parse_args()
    if args.effects_only:
        generate_gameplay_effects()
    else:
        generate_full_audio_pack()
