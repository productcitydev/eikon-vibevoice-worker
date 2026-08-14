import os
import copy
import glob
import http.server
import threading
import torch
import re

from vibevoice import (
    VibeVoiceStreamingForConditionalGenerationInference,
    VibeVoiceStreamingProcessor,
)

MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/VibeVoice-Realtime-0.5B")
VOICES_DIR = os.getenv("VOICES_DIR", "/voices")
OUTPUT_DIR = "/workspace/audition"
SAMPLE_RATE = 24000
TEST_LINE = "There's a phrase attached to one biblical king so often it has become his unofficial title: a man after God's own heart."

os.makedirs(OUTPUT_DIR, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[Audition] Loading model '{MODEL_NAME}' on {device}...")
model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    token=None,
).to(device)
model.eval()

processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_NAME)
print("[Audition] Model loaded.")

woman_voices = sorted(
    [os.path.basename(f).replace(".pt", "")
     for f in glob.glob(os.path.join(VOICES_DIR, "**/*woman*.pt"), recursive=True)]
)

print(f"[Audition] Found {len(woman_voices)} female voices: {woman_voices}")

def start_http_server():
    os.chdir(OUTPUT_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("0.0.0.0", 8888), handler)
    print("[Audition] HTTP server on port 8888")
    server.serve_forever()

threading.Thread(target=start_http_server, daemon=True).start()

index_lines = ["<html><body><h1>VibeVoice Female Voice Audition</h1>"]
index_lines.append(f"<p>Test line: <em>{TEST_LINE}</em></p><hr>")

for voice_name in woman_voices:
    print(f"\n[Audition] Generating: {voice_name}...")

    pt_files = glob.glob(os.path.join(VOICES_DIR, f"**/{voice_name}.pt"), recursive=True)
    if not pt_files:
        print(f"  SKIP — not found")
        continue

    prefilled = torch.load(pt_files[0], map_location=device, weights_only=False)

    inputs = processor.process_input_with_cached_prompt(
        text=TEST_LINE,
        cached_prompt=prefilled,
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
            all_prefilled_outputs=copy.deepcopy(prefilled),
        )

    if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
        out_path = os.path.join(OUTPUT_DIR, f"{voice_name}.wav")
        processor.save_audio(outputs.speech_outputs[0], output_path=out_path)
        print(f"  Saved: {out_path}")
        display = re.sub(r"^en-", "", voice_name).replace("_woman", "")
        index_lines.append(
            f'<div style="margin:20px 0"><h3>{display}</h3>'
            f'<audio controls src="{voice_name}.wav"></audio></div>'
        )
    else:
        print(f"  FAILED — no audio output")

index_lines.append("</body></html>")
with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
    f.write("\n".join(index_lines))

print(f"\n[Audition] Done! {len(woman_voices)} voices generated.")
print("[Audition] Browse http://localhost:8888 to listen.")
print("[Audition] Server running — Ctrl+C to stop.")

import time
while True:
    time.sleep(3600)
