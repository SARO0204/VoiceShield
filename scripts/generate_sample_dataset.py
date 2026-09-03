"""
Sample Dataset Generator for VoiceShield.
Generates speaker-disjoint synthetic and bonafide audio WAV samples for local training pipeline testing.
"""

import os
import sys
import numpy as np
import scipy.io.wavfile as wavfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def generate_sample_dataset(dataset_dir: str = "./datasets", num_speakers: int = 6, samples_per_speaker: int = 4):
    """
    Creates sample audio files organized by speaker for testing speaker-disjoint splitting and training.
    """
    os.makedirs(dataset_dir, exist_ok=True)
    sample_rate = 16000
    duration_sec = 4.0
    num_samples = int(sample_rate * duration_sec)

    created_count = 0

    for s_idx in range(1, num_speakers + 1):
        spk_id = f"spk_{s_idx:03d}"
        spk_dir = os.path.join(dataset_dir, spk_id)
        os.makedirs(spk_dir, exist_ok=True)

        base_freq = 150 + s_idx * 30

        for smp_idx in range(1, samples_per_speaker + 1):
            is_spoof = (smp_idx % 2 == 0)
            label = "spoof" if is_spoof else "bonafide"

            t = np.linspace(0, duration_sec, num_samples, endpoint=False)

            if not is_spoof:
                # Bonafide: harmonic human-like formant synthesis
                audio = (
                    0.5 * np.sin(2 * np.pi * base_freq * t) +
                    0.3 * np.sin(2 * np.pi * base_freq * 2 * t) +
                    0.15 * np.sin(2 * np.pi * base_freq * 3 * t) +
                    0.05 * np.random.normal(0, 0.05, num_samples)
                )
            else:
                # Spoof: phase distorted / artificial vocoder synthesis
                audio = (
                    0.6 * np.sin(2 * np.pi * (base_freq + 20) * t) +
                    0.2 * np.cos(2 * np.pi * (base_freq * 1.5) * t) +
                    0.2 * np.sin(2 * np.pi * (base_freq * 4.2) * t) +
                    0.1 * np.random.normal(0, 0.1, num_samples)
                )

            # Amplitude envelope (fade in/out)
            fade_len = int(sample_rate * 0.1)
            envelope = np.ones(num_samples)
            envelope[:fade_len] = np.linspace(0, 1, fade_len)
            envelope[-fade_len:] = np.linspace(1, 0, fade_len)
            audio = audio * envelope

            # Normalize to 16-bit PCM
            audio = audio / (np.max(np.abs(audio)) + 1e-6)
            audio_int16 = (audio * 32767).astype(np.int16)

            filename = f"{spk_id}_{label}_{smp_idx:02d}.wav"
            file_path = os.path.join(spk_dir, filename)
            wavfile.write(file_path, sample_rate, audio_int16)
            created_count += 1

    print(f"[+] Successfully generated {created_count} sample audio files across {num_speakers} speakers in '{dataset_dir}'.")
    return created_count


if __name__ == "__main__":
    generate_sample_dataset()
