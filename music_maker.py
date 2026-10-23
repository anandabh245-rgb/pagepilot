import array
import math
import random
import wave

SR = 32000
# chords are (semitones above the key note, is_minor)
PROGS = {
    "major": [[(0, 0), (7, 0), (9, 1), (5, 0)],
              [(9, 1), (5, 0), (0, 0), (7, 0)],
              [(0, 0), (9, 1), (5, 0), (7, 0)]],
    "minor": [[(0, 1), (8, 0), (3, 0), (10, 0)],
              [(0, 1), (5, 1), (8, 0), (7, 0)],
              [(0, 1), (10, 0), (8, 0), (10, 0)]],
}
SPECS = {
    "hype": dict(mode="major", bpm=(112, 126), drums="four", arp="pluck16", bass="pump", pad=0.10),
    "synthwave": dict(mode="minor", bpm=(98, 112), drums="half", arp="saw16", bass="pulse8", pad=0.14),
    "trap": dict(mode="minor", bpm=(132, 146), drums="trap", arp="bell", bass="808", pad=0.06),
    "epic": dict(mode="minor", bpm=(80, 96), drums="timp", arp="brass", bass="sub", pad=0.18),
    "news": dict(mode="minor", bpm=(96, 104), drums="light", arp="pluck8", bass="pump", pad=0.10),
    "calm": dict(mode="major", bpm=(66, 76), drums="none", arp="slow", bass="none", pad=0.14),
}
VARIANTS = {
    "hype": ["hype", "synthwave", "epic", "trap", "hype"],
    "news": ["news", "epic"],
    "calm": ["calm"],
}


def freq(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def kick():
    out, ph = [], 0.0
    for i in range(int(0.24 * SR)):
        t = i / SR
        ph += 2 * math.pi * (46 + 100 * math.exp(-t * 30)) / SR
        out.append(math.sin(ph) * math.exp(-t * 13))
    return out


def snare(rng):
    return [(rng.uniform(-1, 1) * 0.8 + 0.5 * math.sin(2 * math.pi * 190 * i / SR))
            * math.exp(-i / SR * 24) for i in range(int(0.18 * SR))]


def hat(rng, decay=90, length=0.05):
    out, prev = [], 0.0
    for i in range(int(length * SR)):
        x = rng.uniform(-1, 1)
        out.append((x - prev) * math.exp(-i / SR * decay))
        prev = x
    return out


def timp(rng):
    out, ph = [], 0.0
    for i in range(int(0.9 * SR)):
        t = i / SR
        ph += 2 * math.pi * (62 + 40 * math.exp(-t * 9)) / SR
        out.append((math.sin(ph) * 0.9 + rng.uniform(-1, 1) * 0.25 * math.exp(-t * 40))
                   * math.exp(-t * 4.2))
    return out


def sub808(f, dur):
    out, ph = [], 0.0
    for i in range(int(dur * SR)):
        t = i / SR
        ph += 2 * math.pi * (f + 38 * math.exp(-t * 22)) / SR
        out.append(math.tanh(2.2 * math.sin(ph)) * math.exp(-t * 2.2))
    return out


def bass_note(f, dur, harm=0.35, decay=2.2):
    n = int(dur * SR)
    return [(math.sin(2 * math.pi * f * i / SR) + harm * math.sin(4 * math.pi * f * i / SR))
            * min(1.0, i / SR / 0.008) * math.exp(-i / SR * decay) * (1 - (i / n) ** 6)
            for i in range(n)]


def pluck(f, decay=8, dur=0.45):
    return [(math.sin(2 * math.pi * f * i / SR) + 0.45 * math.sin(4 * math.pi * f * i / SR)
             + 0.2 * math.sin(6 * math.pi * f * i / SR))
            * min(1.0, i / SR / 0.004) * math.exp(-i / SR * decay)
            for i in range(int(dur * SR))]


def bell(f):
    out = []
    for i in range(int(0.9 * SR)):
        t = i / SR
        m = math.sin(2 * math.pi * f * 3.5 * t) * 2.2 * math.exp(-t * 6)
        out.append(math.sin(2 * math.pi * f * t + m) * math.exp(-t * 3.2))
    return out


def sawish(f, dur, harmonics=7, attack=0.01, decay=1.5):
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        v = sum(math.sin(2 * math.pi * f * k * t) / k for k in range(1, harmonics + 1))
        out.append(v * min(1.0, t / attack) * math.exp(-t * decay) * (1 - (i / n) ** 4))
    return out


def pad(f, dur):
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        env = min(1.0, t / 0.35) * (1 - (i / n) ** 3)
        out.append((math.sin(2 * math.pi * f * t) + math.sin(2 * math.pi * f * 1.003 * t)
                    + 0.4 * math.sin(4 * math.pi * f * t)) * env)
    return out


def whoosh(rng, dur=0.45):
    n = int(dur * SR)
    out, lp = [], 0.0
    for i in range(n):
        lp += 0.25 * (rng.uniform(-1, 1) - lp)
        out.append(lp * (i / n) ** 2 * (1 - (i / n) ** 8))
    return out


def put(buf, start, samples, gain):
    if start < 0:
        return
    end = min(len(buf), start + len(samples))
    for i in range(start, end):
        buf[i] += samples[i - start] * gain


def make_music(style, seconds, path, seed=0):
    rng = random.Random(seed)
    name = rng.choice(VARIANTS.get(style, VARIANTS["hype"]))
    sp = SPECS[name]
    prog = rng.choice(PROGS[sp["mode"]])
    key = 57 + rng.choice([-3, -2, 0, 1, 2, 3, 5])
    bpm = rng.randint(*sp["bpm"])
    beat = 60.0 / bpm
    n = int(seconds * SR)
    buf = [0.0] * n
    K, S = kick(), snare(rng)
    H, H2 = hat(rng), hat(rng, 140, 0.03)
    T = timp(rng)
    for b in range(int(seconds / beat) + 1):
        s0 = int(b * beat * SR)
        half = int(beat / 2 * SR)
        pb = b % 4
        off, minor = prog[(b // 4) % 4]
        root = key + off
        notes = [root, root + (3 if minor else 4), root + 7]
        d = sp["drums"]
        if d == "four":
            put(buf, s0, K, 0.95)
            if pb in (1, 3):
                put(buf, s0, S, 0.45)
            put(buf, s0 + half, H, 0.16)
        elif d == "half":
            if pb in (0, 2):
                put(buf, s0, K, 0.9)
            if pb == 3:
                put(buf, s0 + half, K, 0.6)
            if pb in (1, 3):
                put(buf, s0, S, 0.5)
            put(buf, s0, H, 0.10)
            put(buf, s0 + half, H, 0.14)
        elif d == "trap":
            if pb == 0:
                put(buf, s0, K, 0.9)
            if pb == 2:
                put(buf, s0, S, 0.55)
                put(buf, s0 + half, K, 0.8)
            for k in range(2):
                put(buf, s0 + k * half, H2, 0.14)
            if pb == 3:
                for k in range(4):
                    put(buf, s0 + int(k * beat / 4 * SR), H2, 0.12)
        elif d == "timp":
            if pb == 0:
                put(buf, s0, T, 0.95)
            if pb == 2:
                put(buf, s0, T, 0.55)
            if pb in (1, 3):
                put(buf, s0 + half, H, 0.07)
        elif d == "light":
            if pb in (0, 2):
                put(buf, s0, K, 0.85)
            put(buf, s0 + half, H, 0.14)
        if pb == 0:
            put(buf, s0, pad(freq(root), beat * 4), sp["pad"])
            put(buf, s0, pad(freq(notes[1]), beat * 4), sp["pad"] * 0.8)
            put(buf, s0, pad(freq(notes[2]), beat * 4), sp["pad"] * 0.8)
        bs = sp["bass"]
        if bs == "pump":
            put(buf, s0, bass_note(freq(root - 24), beat * 0.9), 0.55)
            put(buf, s0 + half, bass_note(freq(root - 24), beat * 0.4), 0.38)
        elif bs == "pulse8":
            for k in range(2):
                put(buf, s0 + k * half, sawish(freq(root - 24), beat * 0.45, 5, 0.005, 3.0), 0.30)
        elif bs == "808" and pb in (0, 2):
            put(buf, s0, sub808(freq(root - 24), beat * 1.8), 0.7)
        elif bs == "sub" and pb == 0:
            put(buf, s0, bass_note(freq(root - 24), beat * 3.8, 0.2, 0.6), 0.6)
        ar = sp["arp"]
        seq = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 24]
        if ar == "pluck16":
            for k in range(4):
                put(buf, s0 + int(k * beat / 4 * SR), pluck(freq(seq[(b * 4 + k) % 4])), 0.26)
        elif ar == "saw16":
            for k in range(4):
                m = seq[(b * 4 + k) % 4]
                put(buf, s0 + int(k * beat / 4 * SR), sawish(freq(m), beat * 0.3, 6, 0.004, 5.0), 0.12)
        elif ar == "bell":
            for k in range(2):
                m = seq[(b * 2 + k) % 4] + 12
                put(buf, s0 + k * half, bell(freq(m)), 0.16)
        elif ar == "brass" and pb in (0, 2):
            for m in notes:
                put(buf, s0, sawish(freq(m + 12), beat * 1.8, 8, 0.03, 1.3), 0.10)
        elif ar == "pluck8":
            for k in range(2):
                put(buf, s0 + k * half, pluck(freq(seq[(b * 2 + k) % 4])), 0.24)
        elif ar == "slow" and b % 2 == 0:
            put(buf, s0, pluck(freq(notes[(b // 2) % 3] + 12), 4.5, 0.9), 0.30)
    if name != "calm":
        for t in (3.35, 11.95):
            put(buf, int(t * SR), whoosh(rng), 0.30)
        if name in ("epic", "trap", "synthwave"):
            for t in (3.8, 12.4):
                put(buf, int(t * SR), T if name == "epic" else K, 0.9)
    peak = max(abs(x) for x in buf) or 1.0
    scale = 0.85 / peak
    fade_in, fade_out = int(0.05 * SR), int(1.6 * SR)
    pcm = array.array("h")
    for i, x in enumerate(buf):
        g = scale
        if i < fade_in:
            g *= i / fade_in
        if i > n - fade_out:
            g *= (n - i) / fade_out
        pcm.append(int(max(-1.0, min(1.0, x * g)) * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path
