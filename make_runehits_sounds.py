"""Synthesizes RuneHits' sounds - own sounds, no game audio - shaped after measurements of OSRS sounds on the OSRS
wiki (loudness every 15-30 ms, spectral centroid, energy per band, the strongest frequencies), taken in the browser
and kept only as the numbers in TARGETS below:
magic + goblin (a hit: a wind spell landing, a bright gust of air, and a goblin's raspy squeal as it is hit); fire
(a crit: a bright snap, then a low flickering roar dying in 0.7 s); sword (hit on you: a deep blow and the metal
ringing); splash (a miss: the wiki has no recording of it, made by ear, a soft watery bloop).
Writes sounds/<name>.ogg; any .ogg of your own with the same name plays instead.
Needs: py -m pip install numpy soundfile. Run: py make_runehits_sounds.py (prints mine next to the targets)"""
from pathlib import Path

import numpy as np
import soundfile as sf

ADDON = Path(__file__).parent
RATE = 22050
rng = np.random.default_rng(5)

# what to aim at, measured (rms relative to the loudest frame; centroid weighted by power, but the goblin's by
# magnitude; goblin bands: <250, 250-700, 700-1500, 1500-3500, >3500 Hz)
TARGETS = {
    "goblin": {"hop": 0.02, "rms": [0.62, 0.86, 1.0, 0.63, 0.45, 0.23, 0.09],
               "centroid": [1748, 2264, 1771, 1497, 1722, 1213, 1641],
               "bands": [[3, 20, 27, 42, 9], [3, 18, 21, 40, 18], [4, 27, 31, 26, 12], [4, 36, 37, 14, 9],
                         [5, 32, 37, 11, 15], [12, 51, 19, 8, 9], [29, 40, 5, 8, 18]]},
    "fire": {"hop": 0.03, "rms": [0.92, 1.0, 0.96, 0.85, 0.83, 0.80, 0.70, 0.64, 0.63, 0.41, 0.35, 0.32, 0.30, 0.26,
                                  0.24, 0.24, 0.20, 0.21, 0.18, 0.14, 0.10, 0.06, 0.04],
             "centroid": [358, 476, 451, 437, 402, 281, 238, 212, 216, 181, 214, 141, 169, 233, 135, 240]},
    "wind": {"hop": 0.02, "rms": [0.37, 1.0, 0.86, 0.64, 0.47, 0.35, 0.22, 0.14, 0.12, 0.11, 0.09, 0.07, 0.04, 0.03,
                                  0.02, 0.02],
             "centroid": [3327, 3191, 4151, 4030, 3707, 3060, 1807, 1940, 913, 257, 1477, 2382, 2441, 2471, 2203, 2226]},
    "sword": {"hop": 0.015, "rms": [1.0, 0.70, 0.42, 0.22, 0.15, 0.06, 0.02, 0.03, 0.045, 0.048, 0.045, 0.034, 0.025,
                                    0.023, 0.016],
              "centroid": [635, 239, 259, 307, 195, 552, 2853, 393, 522, 1044, 1115, 1461, 1557, 1231, 1066]},
}


def t(seconds):
    return np.arange(int(RATE * seconds)) / RATE


def lowpass(x, cut):
    """one pole; cut may change sample by sample"""
    cut = np.broadcast_to(cut, x.shape)
    a = np.exp(-2 * np.pi * cut / RATE)
    y, acc = np.empty_like(x), 0.0
    for i, v in enumerate(x):
        acc = (1 - a[i]) * v + a[i] * acc
        y[i] = acc
    return y


def resonator(x, freq, width):
    """a two-pole band-pass (a vowel's formant); freq may glide sample by sample"""
    freq = np.broadcast_to(freq, x.shape)
    r = np.exp(-np.pi * width / RATE)
    y = np.zeros_like(x)
    for i in range(len(x)):
        c1 = 2 * r * np.cos(2 * np.pi * freq[i] / RATE)
        y[i] = (1 - r) * x[i] + c1 * (y[i - 1] if i else 0) - r * r * (y[i - 2] if i > 1 else 0)
    return y


def wind():
    """a wind spell landing: a gust of bright air (3.5-6 kHz) peaking at 20 ms and darkening as it fades, a soft thud
    under it at 180 ms, a faint hiss after"""
    s = t(0.32)
    centre = np.interp(s, [0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.2, 0.32],
                       [3600, 3400, 4700, 4600, 4200, 3400, 1900, 2000, 1000, 1600, 2400])  # measured
    noise = rng.uniform(-1, 1, len(s))
    gust = resonator(noise - lowpass(noise, 900), centre, 1600) * 3      # no rumble under the air
    env = np.interp(s, [0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.2, 0.24, 0.32],
                    [0.37, 1, 0.86, 0.64, 0.47, 0.35, 0.22, 0.14, 0.09, 0.04, 0])
    thud = np.sin(2 * np.pi * 95 * s) * np.exp(-np.abs(s - 0.18) / 0.02) * 0.05
    return gust * env + thud


def sword():
    """a blade landing: a deep blow (86 Hz with partials at 129 and 258 Hz) gone in 75 ms, and the metal ringing at
    2.45 kHz, beating, under it till 220 ms"""
    s = t(0.23)
    w = lambda f: np.sin(2 * np.pi * f * s)
    blow = (w(86) + 0.9 * w(129) + 1.1 * w(258) * np.exp(-s / 0.03)) * np.exp(-s / 0.042)
    hum = w(86) * 0.05 * np.exp(-s / 0.2)                   # the low end lingers under the ring
    click = resonator(rng.uniform(-1, 1, len(s)), 420, 500) * 2.5 * np.exp(-s / 0.007)
    ring = (w(2412) + w(2455) + 0.8 * w(2498) + 0.35 * w(4910)) * np.exp(-np.maximum(0, s - 0.1) / 0.1)
    return blow + hum + click + ring * np.clip((s - 0.07) / 0.03, 0, 1) * 0.045


def splash():
    """a spell splashing on the target - no recording to measure, by ear: a soft watery bloop with a breath of air"""
    s = t(0.28)
    bloop = np.sin(2 * np.pi * np.cumsum(170 + 380 * np.exp(-s / 0.08)) / RATE) * np.exp(-s / 0.07)
    puff = resonator(rng.uniform(-1, 1, len(s)), 1100, 900) * 4 * np.exp(-s / 0.06) * np.minimum(1, s / 0.012)
    return 0.8 * bloop + puff


def goblin():
    """a raspy little voice: pulses at a falling pitch plus breath, through formants gliding from a bright, nasal
    'eh' down to 'uh'; it peaks at 40 ms and is gone by 145 ms"""
    s = t(0.145)
    u = s / s[-1]
    f0 = (190 - 75 * u) * (1 + 0.05 * rng.standard_normal(len(s)))  # jittery: rasp
    phase = np.cumsum(f0) / RATE
    pulses = np.diff(np.floor(phase), prepend=0.0) * 6.0
    fry = 1 + 0.6 * np.sign(np.sin(np.pi * phase))           # every other pulse louder: a growl
    src = pulses * fry + 0.55 * rng.uniform(-1, 1, len(s))
    fast = np.minimum(1, s / 0.07)                           # the bright 'eh' only lasts the first 70 ms
    voice = (1.0 * resonator(src, 900 - 450 * u, 180) + (1.3 - 0.9 * fast) * resonator(src, 2300 - 1150 * fast, 240)
             + (0.9 - 0.8 * fast) * resonator(src, 3100, 340))
    env = np.minimum(1, s / 0.006) * (0.55 + 0.45 * np.minimum(1, s / 0.045)) * np.exp(-np.maximum(0, s - 0.045) / 0.038)
    return voice * env


def fire():
    """a fire spell landing: a bright snap, a short low boom, then a roar of low noise that flickers as it dies"""
    s = t(0.7)
    n = len(s)
    cut = 170 + 560 * np.exp(-s / 0.2)                       # bright for the first 150 ms, then a low roar
    roar = lowpass(lowpass(rng.uniform(-1, 1, n), cut), cut) * 9 * (1 + 1.2 * (1 - np.exp(-s / 0.2)))  # darker, not quieter
    flicker = 1 + 0.7 * lowpass(rng.uniform(-1, 1, n), 18) * 14  # the flames' slow wobble
    snap = lowpass(rng.uniform(-1, 1, n), 3500) * np.exp(-s / 0.008)
    boom = np.sin(2 * np.pi * np.cumsum(55 + 45 * np.exp(-s / 0.05)) / RATE) * np.exp(-s / 0.12)
    crackle = lowpass((rng.random(n) < 12 / RATE) * rng.uniform(-1, 1, n), 900) * 4 * np.exp(-s / 0.3)  # a few pops
    env = np.interp(s, [0, 0.15, 0.24, 0.28, 0.36, 0.48, 0.6, 0.7], [1, 0.85, 0.66, 0.43, 0.33, 0.24, 0.13, 0])  # measured
    return (roar * np.clip(flicker, 0.4, 1.8) + 0.3 * boom + crackle) * env * np.minimum(1, s / 0.004) + 0.25 * snap


def measure(x, hop_s, n=1024, power=True):
    """the same numbers as the browser's: rms per hop, spectral centroid, energy per band (percent)"""
    hop, out = int(RATE * hop_s), []
    for s0 in range(0, len(x) - n // 4, hop):
        w = np.pad(x[s0:s0 + n], (0, max(0, n - len(x[s0:s0 + n]))))
        spec = np.abs(np.fft.rfft(w * np.hanning(n))) ** (2 if power else 1)
        f = np.fft.rfftfreq(n, 1 / RATE)
        bands = [np.sum(spec[(f >= a) & (f < b)]) for a, b in ((0, 250), (250, 700), (700, 1500), (1500, 3500), (3500, 1e9))]
        out.append((np.sqrt(np.mean(w ** 2)), int(np.sum(spec * f) / np.sum(spec)), [round(100 * b / sum(bands)) for b in bands]))
    top = max(o[0] for o in out)
    return [(round(r / top, 2), c, b) for r, c, b in out]


def compare(name, x, n=1024, power=True):
    tg = TARGETS[name]
    print(f"{name} (mine | target):")
    for i, (r, c, b) in enumerate(measure(x, tg["hop"], n, power)):
        if i < len(tg["rms"]):
            tc = tg["centroid"][i] if i < len(tg["centroid"]) else "-"
            tb = f"  bands {b} {tg['bands'][i]}" if "bands" in tg else ""
            print(f"  rms {r:4} {tg['rms'][i]:5}  centroid {c:5} {tc:>5}{tb}")


def save(x, name, gain=0.9):
    x = x / np.max(np.abs(x)) * gain
    sf.write(ADDON / "sounds" / f"{name}.ogg", x.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
    return x


if __name__ == "__main__":
    (ADDON / "sounds").mkdir(parents=True, exist_ok=True)
    g, f, wd, sw = goblin(), fire(), wind(), sword()
    for old in (ADDON / "sounds").glob("*.ogg"):              # names before one file per sound
        if old.stem in ("hit", "crit", "taken", "miss"):
            old.unlink()
    save(wd, "magic", 0.9)                                  # a hit: the spell lands...
    save(g, "goblin", 0.75)                                 # ...and the goblin squeals (played together)
    save(f, "fire", 0.95)                                   # a crit
    save(sw, "sword", 0.9)                                  # hit on you
    save(splash(), "splash", 0.6)                           # a miss
    compare("goblin", g, 512, power=False)
    compare("wind", wd, 512)
    compare("sword", sw, 512)
    compare("fire", f, 2048)
    print("ok")
