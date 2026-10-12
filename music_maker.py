import array
import math
import random
import wave

SR = 32000
STYLES = {
    # bpm, chord roots (midi), qualities, drums, arp
    "hype": {"bpm": 118, "roots": [60, 55, 57, 53], "minor": [0, 0, 1, 0], "drums": 2, "arp": 2},
    "news": {"bpm": 100, "roots": [62, 58, 53, 60], "minor": [1, 0, 0, 0], "drums": 1, "arp": 1},
    "calm": {"bpm": 70, "roots": [57, 53, 60, 55], "minor": [1, 0, 0, 0], "drums": 0, "arp": 0},
}


def freq(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def tri(m, minor):
    return [0, 3 if minor else 4, 7]


def kick():
    out, ph = [], 0.0
    for i in range(int(0.24 * SR)):
        t = i / SR
        ph += 2 * math.pi * (46 + 100 * math.exp(-t * 30)) / SR
        out.append(math.sin(ph) * math.exp(-t * 13))
    return out


def snare(rng):
    out = []
    for i in range(int(0.18 * SR)):
        t = i / SR
        out.append((rng.uniform(-1, 1) * 0.8 + 0.5 * math.sin(2 * math.pi * 190 * t)) * math.exp(-t * 24))
    return out


def hat(rng):
    out, prev = [], 0.0
    for i in range(int(0.05 * SR)):
        t = i / SR
        x = rng.uniform(-1, 1)
        out.append((x - prev) * math.exp(-t * 90))
        prev = x
    return out


def bass(f, dur):
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        env = min(1.0, t / 0.008) * math.exp(-t * 2.2) * (1 - (i / n) ** 6)
        out.append((math.sin(2 * math.pi * f * t) + 0.35 * math.sin(4 * math.pi * f * t)) * env)
    return out


def pluck(f):
    out = []
    for i in range(int(0.45 * SR)):
        t = i / SR
        env = min(1.0, t / 0.004) * math.exp(-t * 8)
        out.append((math.sin(2 * math.pi * f * t) + 0.45 * math.sin(4 * math.pi * f * t)
                    + 0.2 * math.sin(6 * math.pi * f * t)) * env)
    return out


def pad(f, dur):
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        env = min(1.0, t / 0.35) * (1 - (i / n) ** 3)
        v = (math.sin(2 * math.pi * f * t) + math.sin(2 * math.pi * f * 1.003 * t)
             + 0.4 * math.sin(4 * math.pi * f * t))
        out.append(v * env)
    return out


def put(buf, start, samples, gain):
    end = min(len(buf), start + len(samples))
    for i in range(start, end):
        buf[i] += samples[i - start] * gain


def make_music(style, seconds, path, seed=0):
    st = STYLES.get(style, STYLES["hype"])
    rng = random.Random(seed)
    shift = rng.choice([-2, -1, 0, 1, 2, 3])
    bpm = st["bpm"] + rng.choice([-4, 0, 4])
    beat = 60.0 / bpm
    n = int(seconds * SR)
    buf = [0.0] * n
    K, S, H = kick(), snare(rng), hat(rng)
    total_beats = int(seconds / beat) + 1
    bar_beats = 4
    for b in range(total_beats):
        t0 = b * beat
        s0 = int(t0 * SR)
        bar = (b // bar_beats) % 4
        root = st["roots"][bar] + shift
        minor = st["minor"][bar]
        notes = [root + x for x in tri(root, minor)]
        if st["drums"]:
            if st["drums"] == 2 or b % 2 == 0:
                put(buf, s0, K, 0.95)
            if st["drums"] == 2 and b % 2 == 1:
                put(buf, s0, S, 0.45)
            put(buf, s0 + int(beat / 2 * SR), H, 0.16)
            if st["drums"] == 2:
                put(buf, s0, H, 0.10)
        if b % bar_beats == 0:
            put(buf, s0, pad(freq(root), beat * bar_beats), 0.10)
            put(buf, s0, pad(freq(notes[1]), beat * bar_beats), 0.08)
            put(buf, s0, pad(freq(notes[2]), beat * bar_beats), 0.08)
        if st["drums"]:
            put(buf, s0, bass(freq(root - 24), beat * 0.9), 0.55)
            put(buf, s0 + int(beat / 2 * SR), bass(freq(root - 24), beat * 0.4), 0.38)
        if st["arp"]:
            steps = 4 if st["arp"] == 2 else 2
            seq = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 24]
            for k in range(steps):
                m = seq[(b * steps + k) % len(seq)]
                put(buf, s0 + int(k * beat / steps * SR), pluck(freq(m)), 0.26)
        else:
            if b % 2 == 0:
                put(buf, s0, pluck(freq(notes[(b // 2) % 3] + 12)), 0.30)
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
