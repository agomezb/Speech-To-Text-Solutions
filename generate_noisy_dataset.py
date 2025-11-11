#!/usr/bin/env python3
"""
Generate noisy audio dataset by mixing clean voice recordings with noise files.
"""

import os
import random
from pathlib import Path
from pydub import AudioSegment
import typer


app = typer.Typer()


def standardize_audio(audio: AudioSegment) -> AudioSegment:
    """Standardize audio to 16kHz, mono, 16-bit."""
    return audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)


def get_random_noise_segment(noise: AudioSegment, duration_ms: int) -> AudioSegment:
    """Extract a random segment from noise file with specified duration."""
    if len(noise) < duration_ms:
        return None
    
    max_start = len(noise) - duration_ms
    start_pos = random.randint(0, max_start)
    return noise[start_pos:start_pos + duration_ms]


def calculate_noise_gain(voice_dbfs: float, target_snr: int) -> float:
    """Calculate required noise gain to achieve target SNR."""
    target_noise_dbfs = voice_dbfs - target_snr
    return target_noise_dbfs


def mix_audio_at_snr(voice: AudioSegment, noise: AudioSegment, target_snr: int) -> AudioSegment:
    """Mix voice and noise at specified SNR level."""
    # Get random noise segment matching voice duration
    noise_segment = get_random_noise_segment(noise, len(voice))
    
    if noise_segment is None:
        return None
    
    # Calculate required noise level
    voice_dbfs = voice.dBFS
    target_noise_dbfs = calculate_noise_gain(voice_dbfs, target_snr)
    
    # Adjust noise level
    current_noise_dbfs = noise_segment.dBFS
    gain_adjustment = target_noise_dbfs - current_noise_dbfs
    adjusted_noise = noise_segment.apply_gain(gain_adjustment)
    
    # Mix voice and noise
    return voice.overlay(adjusted_noise)


@app.command()
def generate_dataset(
    voice_dir: Path = typer.Option(Path("./audio"), help="Directory containing clean voice recordings"),
    noise_dir: Path = typer.Option(Path("./noise"), help="Directory containing noise files"),
    output_dir: Path = typer.Option(Path("./audio_noise"), help="Output directory for noisy audio files"),
    snr_levels: list[int] = typer.Option([10, 5, 0], help="SNR levels in dB")
):
    """Generate noisy audio dataset by mixing voice and noise files."""
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Get all WAV files
    voice_files = sorted(voice_dir.glob("*.wav"))
    noise_files = sorted(noise_dir.glob("*.wav"))
    
    if not voice_files:
        typer.echo(f"No WAV files found in {voice_dir}", err=True)
        raise typer.Exit(1)
    
    if not noise_files:
        typer.echo(f"No WAV files found in {noise_dir}", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Found {len(voice_files)} voice files and {len(noise_files)} noise files")
    typer.echo(f"Generating mixes at SNR levels: {snr_levels} dB")
    
    total_files = len(voice_files) * len(noise_files) * len(snr_levels)
    processed = 0
    
    # Process each voice file
    for voice_file in voice_files:
        typer.echo(f"\nProcessing voice file: {voice_file.name}")
        voice = standardize_audio(AudioSegment.from_wav(voice_file))
        
        # Mix with each noise file
        for noise_file in noise_files:
            noise = standardize_audio(AudioSegment.from_wav(noise_file))
            
            # Generate mix at each SNR level
            for snr in snr_levels:
                output_name = f"{voice_file.stem}_{noise_file.stem}_{snr}dB.wav"
                output_path = output_dir / output_name
                
                mixed = mix_audio_at_snr(voice, noise, snr)
                
                if mixed is None:
                    typer.echo(f"  ⚠️  Skipping {output_name}: noise file too short", err=True)
                    continue
                
                mixed.export(output_path, format="wav")
                processed += 1
                typer.echo(f"  ✓ Generated: {output_name} ({processed}/{total_files})")
    
    typer.echo(f"\n✅ Dataset generation complete! Generated {processed} files in {output_dir}")


if __name__ == "__main__":
    app()
