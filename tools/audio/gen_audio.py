"""Procedural sound for level 01 (no third-party samples, no licences).

Usage:  python3 tools/audio/gen_audio.py [out_dir]
Writes 16-bit mono WAV files; Unity compresses them to Vorbis on import.
Loops (amb_*, mus_*, *_loop) are made seamless with a cross-fade.
"""
import math
import os
import sys
import wave

import numpy as np

SR = 22050
OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else os.path.join(
    os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Audio")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x, peak=0.9):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x)) or 1.0
    x = x / m * peak
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{name:22s} {len(x) / SR:5.1f}s")


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def spectral_noise(n, shape):
    """Noise with a magnitude spectrum given by shape(freq_hz)."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec *= shape(np.maximum(f, 1.0))
    return np.fft.irfft(spec, n)


def bandpass_fft(x, lo, hi, soft=1.0):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** (2 * soft)) * 1 / (1 + (f / hi) ** (2 * soft))
    return np.fft.irfft(spec * g, len(x))


def onepole_lp(x, cutoff):
    """Time-varying one-pole low-pass, cutoff may be an array (Hz)."""
    c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = a[i] * acc + (1 - a[i]) * x[i]
        y[i] = acc
    return y


def make_loop(x, fade_sec=1.5):
    f = int(fade_sec * SR)
    body = x[:-f].copy()
    tail = x[-f:]
    ramp = np.linspace(0, 1, f)
    body[:f] = body[:f] * ramp + tail * (1 - ramp)
    return body


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)


# ------------------------------------------------------------------ ambience
def sea(sec=34):
    n = int((sec + 1.5) * SR)
    base = spectral_noise(n, lambda f: 1 / f ** 0.9 * (1 / (1 + (f / 900) ** 2)))
    hiss = spectral_noise(n, lambda f: 1 / (1 + (1500 / f) ** 2) / (1 + (f / 6000) ** 2))
    t = np.arange(n) / SR
    swell = np.zeros(n)
    pos = 0.0
    while pos < sec + 1.5:
        period = rng.uniform(5.5, 9.0)
        c = pos + period * 0.55
        swell += np.exp(-((t - c) / (period * 0.22)) ** 2) * rng.uniform(0.6, 1.0)
        pos += period
    swell = 0.25 + swell
    x = base / np.std(base) * swell + 0.35 * hiss / np.std(hiss) * swell ** 2
    save("amb_sea", make_loop(x), 0.8)


def crickets(sec=24):
    n = int((sec + 1.5) * SR)
    x = np.zeros(n)
    for k in range(7):
        f0 = rng.uniform(3900, 5200)
        gain = rng.uniform(0.15, 1.0)
        period = rng.uniform(0.45, 0.9)
        pos = rng.uniform(0, period)
        while pos < sec + 1.4:
            for p in range(rng.integers(2, 4)):
                start = int((pos + p * 0.032) * SR)
                ln = int(0.018 * SR)
                if start + ln >= n:
                    break
                tt = np.arange(ln) / SR
                x[start:start + ln] += gain * np.sin(2 * np.pi * f0 * tt) * np.sin(np.pi * tt / tt[-1]) ** 2
            pos += period * rng.uniform(0.9, 1.1)
            if rng.random() < 0.08:
                pos += rng.uniform(1, 3)
    save("amb_crickets", make_loop(x), 0.6)


def wind(sec=30):
    n = int((sec + 1.5) * SR)
    x = spectral_noise(n, lambda f: 1 / f * (1 / (1 + (f / 500) ** 2)) * (1 / (1 + (60 / f) ** 2)))
    t = np.arange(n) / SR
    mod = 0.5 + 0.35 * np.sin(2 * np.pi * t / 11.0) + 0.15 * np.sin(2 * np.pi * t / 4.3 + 1)
    save("amb_wind", make_loop(x * mod), 0.6)


def lantern_hum(sec=6):
    t = t_axis(sec + 1.5)
    x = sum(np.sin(2 * np.pi * 100 * h * t) / h ** 1.5 for h in range(1, 7))
    x += 0.05 * rng.standard_normal(len(t))
    save("amb_lantern_hum", make_loop(x, 0.5), 0.5)


# ------------------------------------------------------------------ music: distant mandolin waltz
def karplus(freq, dur, bright=0.5, decay=0.996):
    n = int(dur * SR)
    N = max(2, int(SR / freq))
    y = np.zeros(n + N + 1)
    burst = rng.uniform(-1, 1, N)
    burst = burst * bright + np.convolve(burst, [0.5, 0.5], "same") * (1 - bright)
    y[:N] = burst
    k = N
    while k < n + N:
        end = min(k + N, n + N)
        prev = y[k - N:end - N]
        prev2 = y[k - N - 1:end - N - 1] if k - N - 1 >= 0 else np.concatenate([[0], y[k - N:end - N - 1]])
        y[k:end] = decay * 0.5 * (prev + prev2)
        k = end
    return y[N:N + n]


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name):
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[pitch] + (octave - 4) * 12 - 9) / 12)


def waltz():
    bpm = 104
    beat = 60 / bpm
    chords = [("A2", ["A3", "C4", "E4"]), ("A2", ["A3", "C4", "E4"]), ("D3", ["D4", "F4", "A4"]), ("D3", ["D4", "F4", "A4"]),
              ("E2", ["E3", "G#3", "B3"]), ("E2", ["E3", "G#3", "D4"]), ("A2", ["A3", "C4", "E4"]), ("E2", ["E3", "G#3", "B3"]),
              ("F2", ["F3", "A3", "C4"]), ("C3", ["C4", "E4", "G4"]), ("D3", ["D4", "F4", "A4"]), ("E2", ["E3", "G#3", "B3"]),
              ("A2", ["A3", "C4", "E4"]), ("D3", ["D4", "F4", "A4"]), ("E2", ["E3", "G#3", "B3"]), ("A2", ["A3", "C4", "E4"])]
    melody = [("E5", 2), ("D5", 1), ("C5", 2), ("B4", 1), ("A4", 3), ("F5", 2), ("E5", 1),
              ("D5", 3), ("B4", 2), ("C5", 1), ("D5", 2), ("E5", 1), ("B4", 3),
              ("A4", 2), ("C5", 1), ("E5", 3), ("F5", 2), ("E5", 1), ("D5", 3),
              ("C5", 2), ("D5", 1), ("E5", 2), ("D5", 1), ("B4", 2), ("G#4", 1), ("A4", 3)]  # 16 bars of 3/4
    total = len(chords) * 3 * beat
    n = int((total + 3) * SR)
    x = np.zeros(n)

    def put(sig, at, gain):
        s = int(at * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        x[s:e] += sig[:e - s] * gain

    for i, (bass, tri) in enumerate(chords):
        t0 = i * 3 * beat
        put(karplus(hz(bass), 2.5, 0.3, 0.997), t0, 0.9)
        for b in (1, 2):
            for j, note in enumerate(tri):
                put(karplus(hz(note), 1.2, 0.5, 0.994), t0 + b * beat + j * 0.012, 0.32)
    t = 0.0
    for note, beats in melody:
        dur = beats * beat
        f = hz(note)
        # mandolin tremolo on long notes
        step = 0.11 if beats >= 2 else dur
        k = 0.0
        while k < dur - 0.02:
            put(karplus(f, 0.5, 0.75, 0.993), t + k, 0.45 * (1 - 0.15 * (k > 0)))
            k += step
        t += dur
    # lay the 3-second tail over the start so the loop is seamless
    body = x[:int(total * SR)].copy()
    tail = x[int(total * SR):]
    body[:len(tail)] += tail
    body = bandpass_fft(body, 120, 4200, 1.0)
    save("mus_cafe_waltz", body, 0.7)


# ------------------------------------------------------------------ one-shots
def bell():
    t = t_axis(7.0)
    f0 = 196.0
    x = np.zeros_like(t)
    for ratio, amp, dec in ((0.5, 0.6, 4.5), (1.0, 1.0, 3.5), (1.19, 0.5, 2.5), (1.5, 0.45, 2.0), (2.0, 0.4, 1.6),
                            (2.5, 0.25, 1.2), (3.0, 0.2, 0.9), (4.2, 0.12, 0.6)):
        x += amp * np.sin(2 * np.pi * f0 * ratio * t + rng.uniform(0, 6)) * np.exp(-t / dec)
    x *= np.minimum(1, t / 0.004)
    save("sfx_bell_far", bandpass_fft(x, 80, 3000), 0.8)


def footsteps():
    for i in range(4):
        n = int(0.09 * SR)
        x = rng.standard_normal(n) * env(n, 0.002, 0.018)
        x = bandpass_fft(x, 120, rng.uniform(900, 1400))
        wet = rng.standard_normal(n) * env(n, 0.012, 0.01) * 0.25
        x = x + bandpass_fft(np.roll(wet, int(0.01 * SR)), 2500, 6000)
        save(f"sfx_step_{i + 1}", x, 0.7)
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    metal = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, d in ((420, 0.08), (1130, 0.05), (2310, 0.03)))
    metal += rng.standard_normal(n) * env(n, 0.001, 0.01)
    save("sfx_step_metal", metal, 0.6)


def jump_land():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n) * np.sin(np.pi * t / t[-1]) ** 2
    x = onepole_lp(x, 600 + 2500 * t / t[-1])
    save("sfx_jump", x, 0.5)
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (90 - 40 * t / t[-1]) * t) * np.exp(-t / 0.05)
    thud += bandpass_fft(rng.standard_normal(n) * env(n, 0.001, 0.03), 100, 1500) * 0.6
    save("sfx_land", thud, 0.7)


FORMANTS = {"i": (310, 2300, 2900), "a": (750, 1250, 2600), "u": (350, 800, 2400), "e": (500, 1800, 2600)}


def formant_voice(f0_curve, vowels, gain_curve):
    """Simple source-filter voice: band-limited pulse train through moving formants (frequency domain per block)."""
    n = len(f0_curve)
    phase = np.cumsum(f0_curve) / SR
    src = np.zeros(n)
    for h in range(1, 24):
        src += np.sin(2 * np.pi * h * phase) / h * (h * f0_curve < SR * 0.45)
    src *= gain_curve
    out = np.zeros(n)
    block = 512
    hop = 256
    win = np.hanning(block)
    f = np.fft.rfftfreq(block, 1 / SR)
    for start in range(0, n - block, hop):
        pos = start / max(1, n - block)
        k = min(len(vowels) - 1, pos * (len(vowels) - 1))
        a, b = vowels[int(k)], vowels[min(len(vowels) - 1, int(k) + 1)]
        frac = k - int(k)
        F = [FORMANTS[a][i] * (1 - frac) + FORMANTS[b][i] * frac for i in range(3)]
        g = sum(np.exp(-((f - fc) / (fc * 0.12)) ** 2) * amp for fc, amp in zip(F, (1.0, 0.6, 0.25)))
        spec = np.fft.rfft(src[start:start + block] * win) * g
        out[start:start + block] += np.fft.irfft(spec, block) * win
    return out


def meows():
    for i, (dur, f_start, f_peak, f_end, vow) in enumerate((
            (0.75, 520, 780, 480, ["i", "e", "a", "u"]),
            (0.5, 600, 820, 650, ["e", "a", "u"]),
            (1.0, 450, 700, 380, ["i", "a", "a", "u"]))):
        n = int(dur * SR)
        t = np.arange(n) / dur / SR
        f0 = np.interp(t, [0, 0.35, 1], [f_start, f_peak, f_end]) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t * dur))
        gain = np.sin(np.pi * np.clip(t * 1.05, 0, 1)) ** 0.6
        save(f"sfx_meow_{i + 1}", formant_voice(f0, vow, gain), 0.8)
    # Baron: lower, lazier
    n = int(1.1 * SR)
    t = np.arange(n) / n
    f0 = np.interp(t, [0, 0.4, 1], [330, 470, 300])
    save("sfx_meow_baron", formant_voice(f0, ["e", "a", "u", "u"], np.sin(np.pi * t) ** 0.7), 0.8)


def purr(sec=4):
    n = int((sec + 0.5) * SR)
    t = np.arange(n) / SR
    rate = 26 + 2 * np.sin(2 * np.pi * t / 2.2)
    pulses = np.maximum(0, np.sin(2 * np.pi * np.cumsum(rate) / SR)) ** 3
    breath = 0.6 + 0.4 * np.sin(2 * np.pi * t / 2.2) ** 2
    x = bandpass_fft(rng.standard_normal(n), 40, 380) * pulses * breath
    save("sfx_purr_loop", make_loop(x, 0.5), 0.7)


def misc():
    # water drip "plink"
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    f = 1600 * np.exp(-t * 9) + 700
    save("sfx_drip", np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05) * np.minimum(1, t / 0.002), 0.5)
    # ceramic pot breaking
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    x = bandpass_fft(rng.standard_normal(n), 400, 7000) * env(n, 0.001, 0.08)
    for _ in range(14):
        s = int(rng.uniform(0, 0.25) * SR)
        fr = rng.uniform(1800, 5200)
        ln = n - s
        x[s:] += 0.3 * np.sin(2 * np.pi * fr * t[:ln]) * np.exp(-t[:ln] / rng.uniform(0.03, 0.12))
    save("sfx_pot_break", x, 0.8)
    # checkpoint chime (two soft bell notes)
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, fr in enumerate((880.0, 1318.5)):
        s = int(k * 0.14 * SR)
        tt = t[:n - s]
        x[s:] += sum(np.sin(2 * np.pi * fr * r * tt) * a for r, a in ((1, 1), (2.76, 0.3), (5.4, 0.1))) * np.exp(-tt / 0.5)
    save("sfx_chime", x, 0.5)
    # rope / wire creak
    n = int(0.8 * SR)
    t = np.arange(n) / SR
    fr = 180 + 60 * np.sin(2 * np.pi * 1.3 * t)
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * (rng.random(n) < 0.3) * np.sin(np.pi * t / t[-1])
    save("sfx_rope_creak", bandpass_fft(x, 150, 2500), 0.4)
    # pigeons: wing flaps and coo
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    flaps = np.maximum(0, np.sin(2 * np.pi * 11 * t)) ** 6 * np.exp(-t / 0.5)
    save("sfx_pigeon_flap", bandpass_fft(rng.standard_normal(n), 300, 3500) * flaps, 0.6)
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    coo = np.sin(2 * np.pi * (380 + 40 * np.sin(2 * np.pi * 1.5 * t)) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 5 * t)) * np.sin(np.pi * t / t[-1])
    save("sfx_pigeon_coo", bandpass_fft(coo, 200, 1500), 0.4)
    # UI tap
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    save("sfx_ui_tap", np.sin(2 * np.pi * 1200 * t) * np.exp(-t / 0.012), 0.4)


ALL = [sea, crickets, wind, lantern_hum, waltz, bell, footsteps, jump_land, meows, purr, misc]

if __name__ == "__main__":
    only = set(sys.argv[2:])
    for fn in ALL:
        if not only or fn.__name__ in only:
            fn()
