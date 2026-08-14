import os
import io
import copy
import base64
import glob
import torch
import runpod

from vibevoice import (
    VibeVoiceStreamingForConditionalGenerationInference,
    VibeVoiceStreamingProcessor,
)

MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/VibeVoice-1.5B")
DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "en")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "en-Grace_woman")
HF_TOKEN = os.getenv("HF_TOKEN", None)
VOICES_DIR = os.getenv("VOICES_DIR", "/voices")
SAMPLE_RATE = 24000

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[VibeVoice] Loading model '{MODEL_NAME}' on {device}...")
model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    attn_implementation="sdpa",
    token=HF_TOKEN,
)
model.eval()
model.set_ddpm_inference_steps(num_steps=5)

processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_NAME, token=HF_TOKEN)
print("[VibeVoice] Model loaded.")

voice_cache = {}

def load_voice(voice_name: str):
    if voice_name in voice_cache:
        return voice_cache[voice_name]

    pt_path = os.path.join(VOICES_DIR, f"{voice_name}.pt")
    if not os.path.exists(pt_path):
        available = [os.path.basename(f).replace(".pt", "") for f in glob.glob(os.path.join(VOICES_DIR, "*.pt"))]
        raise FileNotFoundError(f"Voice '{voice_name}' not found. Available: {available}")

    prefilled = torch.load(pt_path, map_location=device, weights_only=False)

    voice_cache[voice_name] = prefilled
    print(f"[VibeVoice] Loaded voice: {voice_name}")
    return prefilled


def synthesize(text: str, voice_name: str) -> bytes:
    prefilled = load_voice(voice_name)

    inputs = processor.process_input_with_cached_prompt(
        text=text,
        cached_prompt=prefilled,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    inputs = {
        k: v.to(device) if hasattr(v, "to") else v
        for k, v in inputs.items()
    }

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
        audio = outputs.speech_outputs[0]
    else:
        raise RuntimeError("Model returned no speech output")

    buf = io.BytesIO()
    processor.save_audio(audio, output_path=buf)
    buf.seek(0)
    return buf.read()


def handler(job):
    job_input = job.get("input", {})
    text = job_input.get("text")
    voice = job_input.get("voice", DEFAULT_VOICE)

    if not isinstance(text, str) or not text.strip():
        return {"error": "Missing required 'text' (non-empty string)."}

    try:
        audio_bytes = synthesize(text.strip(), voice)
        return {
            "voice": voice,
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        }
    except Exception as e:
        raise RuntimeError(f"Inference failed: {e}")


runpod.serverless.start({"handler": handler})
