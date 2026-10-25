"""Original procedural soundtrack for LASTLIGHT. No external samples."""
from pathlib import Path
import wave
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'audio'
OUT.mkdir(exist_ok=True)
RATE = 48000
DURATION = 62
N = RATE * DURATION
time = np.arange(N, dtype=np.float64) / RATE
rng = np.random.default_rng(20261025)

def ramp(start, end, t):
    return np.clip((t - start) / (end - start), 0.0, 1.0)

def soft_pulse(at, length, frequency, gain, decay=3.0):
    i0 = max(0, round(at * RATE))
    count = min(N - i0, round(length * RATE))
    if count <= 0:
        return
    local = np.arange(count) / RATE
    env = (1 - np.exp(-local * 35)) * np.exp(-local * decay)
    sweep = frequency * (1 - .28 * ramp(.0, length, local))
    phase = 2 * np.pi * np.cumsum(sweep) / RATE
    bed[i0:i0 + count] += gain * env * (np.sin(phase) + .3 * np.sin(2 * phase))

def whoosh(at, length, gain):
    i0 = round(at * RATE)
    count = min(N - i0, round(length * RATE))
    if count <= 0:
        return
    local = np.arange(count) / RATE
    noise = rng.standard_normal(count)
    smoothed = np.convolve(noise, np.ones(37) / 37, mode='same')
    env = np.sin(np.pi * local / length) ** 2
    bed[i0:i0 + count] += gain * env * smoothed

# Restrained low electronic atmosphere with slow harmonic movement.
chord = (
    .10 * np.sin(2 * np.pi * 55 * time) +
    .065 * np.sin(2 * np.pi * 82.4069 * time + .25 * np.sin(2 * np.pi * .12 * time)) +
    .035 * np.sin(2 * np.pi * 110 * time) +
    .025 * np.sin(2 * np.pi * 164.8138 * time)
)
envelope = .28 + .33 * ramp(3, 8, time) + .17 * ramp(29, 39, time)
envelope *= (1 - .94 * (ramp(12.8, 13.25, time) - ramp(14.0, 15.4, time)))
envelope *= (1 - ramp(60.5, 62, time))
bed = chord * envelope

# Dark opening, power loss, tension and outcome cues.
soft_pulse(.30, 2.0, 67, .28, 2.6)
soft_pulse(2.05, 1.6, 54, .24, 3.4)
whoosh(3.55, .65, .27)
for beat in [4.3, 5.7, 7.2, 9.0, 10.7]:
    soft_pulse(beat, .7, 130, .055, 6)
whoosh(11.55, .7, .34)
soft_pulse(13.05, 2.2, 46, .50, 2.2)
for beat in np.arange(21.6, 28.8, .77):
    soft_pulse(float(beat), .4, 96 + (beat - 21.6) * 6, .055 + .008 * (beat - 21.6), 8)
whoosh(28.45, .48, .20)
soft_pulse(29.05, 2.1, 48, .42, 2.3)
soft_pulse(32.0, 1.3, 73, .21, 3)
soft_pulse(35.15, 1.3, 97, .24, 3)
whoosh(38.55, .55, .19)
for beat in [40.5, 42.1, 43.7, 45.1]:
    soft_pulse(beat, .7, 130, .12, 5)
soft_pulse(45.2, 3, 65.4, .38, 1.2)
whoosh(47.65, .48, .16)
for beat in [48.4, 49.2, 50.0, 50.8, 51.6, 52.4]:
    soft_pulse(beat, .27, 220, .045, 12)
soft_pulse(54.75, 1.1, 98, .18, 4)
whoosh(58.6, .5, .20)
soft_pulse(59.0, 2.5, 55, .43, 1.5)
soft_pulse(59.06, 2.5, 82.4069, .17, 1.6)

# Gentle stereo width without phase-cancelled mono output.
left = np.tanh(bed * 1.15)
right = np.tanh((np.roll(bed, 47) * .96 + bed * .04) * 1.15)
stereo = np.stack([left, right], axis=1)
peak = float(np.max(np.abs(stereo)))
if peak > .93:
    stereo *= .93 / peak

def write(path, scale):
    pcm = np.int16(np.clip(stereo * scale, -.99, .99) * 32767)
    with wave.open(str(path), 'wb') as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(pcm.tobytes())

write(OUT / 'original-full.wav', 1.0)
write(OUT / 'original-speech-safe.wav', .36)
print({'duration': DURATION, 'sample_rate': RATE, 'peak': peak, 'license': 'Original procedural synthesis for LASTLIGHT'})
