"""Lager reel-lyden (egen musikk, 120 BPM, 17 s) som WAV. Ingen samples, alt syntetisert med numpy."""
import wave
import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
BEATS = 34
DUR = BEATS * BEAT + 1.0  # + hale


def tvec(n):
    return np.arange(int(n * SR)) / SR


def put(buf, t0, sig, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= buf.shape[1]:
        return
    sig = sig[: buf.shape[1] - i]
    buf[0, i:i + len(sig)] += sig * gain * (1 - max(0, pan))
    buf[1, i:i + len(sig)] += sig * gain * (1 + min(0, pan))


def kick():
    t = tvec(0.45)
    f = 48 + 130 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(1.6 * np.sin(ph)) * np.exp(-t * 7.5)


def clap(rng):
    out = np.zeros(int(0.3 * SR))
    for off in (0, 0.011, 0.022):
        n = rng.standard_normal(int(0.2 * SR))
        n = np.diff(n, prepend=0)  # grovt høypass
        t = tvec(0.2)
        i = int(off * SR)
        out[i:i + len(n)] += n * np.exp(-t * (28 if off < 0.022 else 14))
    return out * 0.5


def hat(rng, open_=False):
    n = rng.standard_normal(int((0.25 if open_ else 0.07) * SR))
    n = np.diff(np.diff(n, prepend=0), prepend=0)
    t = tvec(len(n) / SR)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.35


def saw(f, t, harm=10):
    return sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, harm + 1) if f * k < 9000) * 0.6


def bass_note(f, dur):
    t = tvec(dur)
    s = saw(f, t, 6) + 0.5 * np.sin(2 * np.pi * f * t)
    env = np.minimum(1, t * 200) * np.exp(-t * 3.5)
    return np.tanh(s * 1.4) * env


def stab(freqs, dur=0.22):
    t = tvec(dur)
    s = sum(saw(f, t, 8) + saw(f * 1.006, t, 8) for f in freqs) / len(freqs)
    return s * np.minimum(1, t * 300) * np.exp(-t * 11)


def lead(f, dur=0.2):
    t = tvec(dur)
    s = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + saw(f, t, 5) * 0.4
    return s * np.minimum(1, t * 400) * np.exp(-t * 9)


def hz(n):  # midi
    return 440 * 2 ** ((n - 69) / 12)


def riser(dur, rng):
    t = tvec(dur)
    n = np.diff(rng.standard_normal(len(t)), prepend=0)
    return n * (t / dur) ** 2 * 0.5 + np.sin(2 * np.pi * (200 + 1800 * (t / dur) ** 2) * t) * (t / dur) * 0.15


def crash(rng, dur=1.4):
    n = rng.standard_normal(int(dur * SR))
    n = np.diff(np.diff(n, prepend=0), prepend=0)
    t = tvec(dur)
    return n * np.exp(-t * 3.2) * 0.5


def lag():
    rng = np.random.default_rng(7)
    buf = np.zeros((2, int(DUR * SR)))
    kick_buf = np.zeros(buf.shape[1])
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]  # Am F C G (bass-rot, akkord)
    k = kick()
    for b in range(BEATS - 2 + 1):  # siste slag (32) er sluttkrasjen
        t0 = b * BEAT
        if b == 32:
            break
        put(buf, t0, k, 1.0)
        kick_buf[int(t0 * SR):int(t0 * SR) + 3000] = 1
    # hook (slag 0-3): kick + riser + crash på 0
    put(buf, 0, crash(rng), 0.8)
    put(buf, 2 * BEAT, riser(2 * BEAT, rng), 0.9)
    for b in range(4, 32):
        t0 = b * BEAT
        if b % 2 == 1:
            put(buf, t0, clap(rng), 0.9)
        put(buf, t0 + BEAT / 2, hat(rng, b % 4 == 3), 0.8, pan=0.15)
        put(buf, t0, hat(rng), 0.35, pan=-0.15)
    for b in range(1, 4):
        if b % 2 == 1:
            put(buf, b * BEAT, clap(rng), 0.7)
        put(buf, b * BEAT + BEAT / 2, hat(rng), 0.7)
    # bass, stab, lead fra slag 4 (hook har bare trommer)
    for b in range(4, 32):
        bar = (b // 4) % 4
        root, chord = prog[bar]
        t0 = b * BEAT
        for h in range(2):  # åttedeler
            note = root + (12 if h == 1 and b % 2 else 0)
            put(buf, t0 + h * BEAT / 2, bass_note(hz(note), BEAT / 2 * 0.95), 0.9)
        if b % 2 == 1:  # offbeat-stab
            put(buf, t0 + BEAT / 2, stab([hz(n + 12) for n in chord]), 0.55, pan=0.2)
        if b >= 8:  # arpeggio fra slag 8
            for s in range(4):
                n = chord[(s + b) % 3] + 24
                put(buf, t0 + s * BEAT / 4, lead(hz(n)), 0.22, pan=(-0.3 if s % 2 else 0.3))
    # sluttkrasj
    put(buf, 32 * BEAT, k, 1.2)
    put(buf, 32 * BEAT, crash(rng, 1.6), 1.0)
    put(buf, 32 * BEAT, bass_note(hz(33), 1.0), 1.0)
    put(buf, 32 * BEAT, stab([hz(57), hz(64), hz(69)], 0.9), 0.6)
    # sidechain: bass/stab/lead dukker for kick (enkelt: kick_buf glatter)
    duck = np.convolve(kick_buf, np.exp(-np.arange(0, 6000) / 1500.0))[: buf.shape[1]]
    duck = 1 - 0.55 * np.clip(duck, 0, 1)
    # kick ligger allerede i buf; dukk alt og legg kick på igjen
    kk = np.zeros_like(buf)
    for b in range(32):
        put(kk, b * BEAT, k, 1.0)
    put(kk, 32 * BEAT, k, 1.2)
    rest = buf - kk
    out = rest * duck + kk
    out /= np.max(np.abs(out)) * 1.05
    out = np.tanh(out * 1.3) / np.tanh(1.3)
    fade = np.ones(out.shape[1])
    fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
    return out * fade


def skriv(fil):
    a = (lag() * 32000).astype(np.int16).T
    with wave.open(str(fil), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a.tobytes())


if __name__ == "__main__":
    import sys
    skriv(sys.argv[1] if len(sys.argv) > 1 else "reel.wav")
