import os
import re
import copy
import glob
import http.server
import threading
import tempfile
import time
import torch
import soundfile as sf
import numpy as np

from vibevoice import (
    VibeVoiceStreamingForConditionalGenerationInference,
    VibeVoiceStreamingProcessor,
)

MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/VibeVoice-Realtime-0.5B")
VOICES_DIR = os.getenv("VOICES_DIR", "/voices")
SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "/scripts")
OUTPUT_DIR = "/workspace/narrations"
VOICE = os.getenv("VOICE", "en-Emma_woman")
SAMPLE_RATE = 24000

os.makedirs(OUTPUT_DIR, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[Batch] Loading model '{MODEL_NAME}' on {device}...")
model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    token=None,
).to(device)
model.eval()

processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_NAME)
print("[Batch] Model loaded.")

voice_path = glob.glob(os.path.join(VOICES_DIR, f"**/{VOICE}.pt"), recursive=True)
if not voice_path:
    raise FileNotFoundError(f"Voice '{VOICE}' not found in {VOICES_DIR}")
prefilled_base = torch.load(voice_path[0], map_location=device, weights_only=False)
print(f"[Batch] Loaded voice: {VOICE}")


def strip_metadata(text):
    parts = text.split("---", 1)
    if len(parts) > 1:
        return parts[1].strip()
    return text.strip()


def strip_tags(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def split_paragraphs(text):
    return [p.strip() for p in text.split('\n\n') if p.strip()]


def generate_audio(text_chunk):
    inputs = processor.process_input_with_cached_prompt(
        text=text_chunk,
        cached_prompt=prefilled_base,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=None,
            cfg_scale=3.0,
            tokenizer=processor.tokenizer,
            generation_config={"do_sample": False},
            all_prefilled_outputs=copy.deepcopy(prefilled_base),
        )

    if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
        return outputs.speech_outputs[0]
    return None


def save_audio_tensor(audio_tensor, out_path):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        processor.save_audio(audio_tensor, output_path=tmp_path)
        data, sr = sf.read(tmp_path)
        sf.write(out_path, data, sr)
    finally:
        os.unlink(tmp_path)


def process_episode(script_path):
    with open(script_path) as f:
        raw = f.read()

    narration = strip_metadata(raw)
    narration = strip_tags(narration)
    word_count = len(narration.split())

    paragraphs = split_paragraphs(narration)

    audio_chunks = []
    silence = np.zeros(int(SAMPLE_RATE * 0.6))

    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        print(f"    Paragraph {i+1}/{len(paragraphs)} ({len(para.split())} words)...")

        audio = generate_audio(para)
        if audio is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                processor.save_audio(audio, output_path=tmp_path)
                data, _ = sf.read(tmp_path)
                audio_chunks.append(data)
                audio_chunks.append(silence)
            finally:
                os.unlink(tmp_path)
        else:
            print(f"    WARNING: no audio for paragraph {i+1}")

    if audio_chunks:
        if len(audio_chunks) > 1:
            audio_chunks = audio_chunks[:-1]
        full_audio = np.concatenate(audio_chunks)
        return full_audio, word_count
    return None, word_count


def start_http_server():
    os.chdir(OUTPUT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("0.0.0.0", 8888), handler)
    print("[Batch] HTTP server on port 8888")
    server.serve_forever()

threading.Thread(target=start_http_server, daemon=True).start()

scripts = sorted(glob.glob(os.path.join(SCRIPTS_DIR, "[0-9]*.md")))
print(f"[Batch] Found {len(scripts)} episode scripts")

progress = {"total": len(scripts), "completed": 0, "failed": 0, "current": "", "results": []}


def update_index():
    lines = [
        "<html><head><title>Eikon Narrations</title>",
        '<meta http-equiv="refresh" content="30">',
        "<style>body{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 20px}"
        "audio{width:100%}.ep{margin:24px 0;padding:16px;border:1px solid #ddd;border-radius:8px}"
        ".stats{color:#666;font-size:14px}</style></head><body>",
        "<h1>Eikon Episode Narrations</h1>",
        f"<p>Voice: <strong>{VOICE}</strong> | "
        f"Progress: <strong>{progress['completed']}/{progress['total']}</strong>"
        f" | Failed: {progress['failed']}</p>",
    ]
    if progress['current']:
        lines.append(f"<p><em>Currently generating: {progress['current']}...</em></p>")
    lines.append("<hr>")
    for r in reversed(progress['results']):
        lines.append(
            f'<div class="ep"><h3>{r["name"]}</h3>'
            f'<p class="stats">{r["words"]} words | {r["duration"]:.1f}s audio | '
            f'generated in {r["gen_time"]:.1f}s</p>'
            f'<audio controls src="{r["file"]}"></audio></div>'
        )
    lines.append("</body></html>")
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
        f.write("\n".join(lines))


update_index()
batch_start = time.time()

for i, script_path in enumerate(scripts):
    name = os.path.basename(script_path).replace(".md", "")
    print(f"\n[Batch] [{i+1}/{len(scripts)}] Generating: {name}...")
    progress['current'] = name
    update_index()

    start_time = time.time()
    try:
        audio, word_count = process_episode(script_path)
        gen_time = time.time() - start_time

        if audio is not None:
            out_file = f"{name}.wav"
            out_path = os.path.join(OUTPUT_DIR, out_file)
            sf.write(out_path, audio, SAMPLE_RATE)

            duration = len(audio) / SAMPLE_RATE
            progress['completed'] += 1
            progress['results'].append({
                "name": name,
                "file": out_file,
                "words": word_count,
                "duration": duration,
                "gen_time": gen_time,
            })
            print(f"  Done: {duration:.1f}s audio, {word_count} words, generated in {gen_time:.1f}s")
        else:
            progress['failed'] += 1
            print(f"  FAILED — no audio output")
    except Exception as e:
        progress['failed'] += 1
        gen_time = time.time() - start_time
        print(f"  ERROR: {e} (after {gen_time:.1f}s)")

    update_index()

progress['current'] = ""
total_time = time.time() - batch_start
update_index()

print(f"\n[Batch] All done! {progress['completed']}/{progress['total']} episodes generated "
      f"({progress['failed']} failed) in {total_time:.0f}s ({total_time/60:.1f} min)")
print("[Batch] Browse http://localhost:8888 to listen.")

while True:
    time.sleep(3600)
