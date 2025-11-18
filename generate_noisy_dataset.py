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

# fijamos la semilla para resultados consistentes
random.seed(42)

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


def mix_audio_at_snr(voice: AudioSegment, noise_segment: AudioSegment, target_snr: int) -> AudioSegment:
    """Mix voice and noise segment at specified SNR level."""
    # Calculate required noise level
    safe_voice = voice.normalize() # Normaliza a 0 dB primero
    safe_voice = safe_voice.apply_gain(-10.0) # Bajamos a -10 dB (Headroom)

    voice_dbfs = safe_voice.dBFS
    target_noise_dbfs = voice_dbfs - target_snr
    
    # Adjust noise level
    current_noise_dbfs = noise_segment.dBFS
    gain_adjustment = target_noise_dbfs - current_noise_dbfs
    adjusted_noise = noise_segment.apply_gain(gain_adjustment)
    
    # Mix voice and noise
    return safe_voice.overlay(adjusted_noise)


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
    
    # Preload all noise files into memory (optimization)
    typer.echo("\nPreloading noise files into memory...")
    noise_data = {}
    for noise_file in noise_files:
        noise_data[noise_file.stem] = standardize_audio(AudioSegment.from_wav(noise_file))
        typer.echo(f"  ✓ Loaded: {noise_file.name}")
    
    # Total files = clean versions + noisy versions
    total_files = len(voice_files) + (len(voice_files) * len(noise_files) * len(snr_levels))
    processed = 0
    clean_files = 0
    
    # Process each voice file
    for voice_file in voice_files:
        typer.echo(f"\nProcessing voice file: {voice_file.name}")
        voice = standardize_audio(AudioSegment.from_wav(voice_file))
        
        # Export clean version (normalized with same headroom as noisy versions)
        clean_voice = voice.normalize().apply_gain(-10.0)
        clean_output_path = output_dir / f"{voice_file.stem}_clean.wav"
        clean_voice.export(clean_output_path, format="wav")
        clean_files += 1
        typer.echo(f"  ✓ Exported clean version: {voice_file.stem}_clean.wav")
        
        # Mix with each noise file (using preloaded noise from memory)
        for noise_file in noise_files:
            noise = noise_data[noise_file.stem]  # Get from memory instead of loading from disk
            
            # Get ONE random noise segment for this voice-noise pair
            noise_segment = get_random_noise_segment(noise, len(voice))
            
            if noise_segment is None:
                typer.echo(f"  ⚠️  Skipping {voice_file.stem}_{noise_file.stem}: noise file too short", err=True)
                continue
            
            # Generate mix at each SNR level using the SAME noise segment
            for snr in snr_levels:
                output_name = f"{voice_file.stem}_{noise_file.stem}_{snr}dB.wav"
                output_path = output_dir / output_name
                
                mixed = mix_audio_at_snr(voice, noise_segment, snr)
                mixed.export(output_path, format="wav")
                processed += 1
                typer.echo(f"  ✓ Generated: {output_name} ({processed + clean_files}/{total_files})")
    
    typer.echo(f"\n✅ Dataset generation complete!")
    typer.echo(f"   - Clean files: {clean_files}")
    typer.echo(f"   - Noisy files: {processed}")
    typer.echo(f"   - Total: {processed + clean_files} files in {output_dir}")


if __name__ == "__main__":
    app()
