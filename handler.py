import os
import io
import base64
import torch
import torchaudio
import numpy as np
import runpod

from vibevoice import (
    VibeVoiceStreamingForConditionalGenerationInference,
    VibeVoiceStreamingProcessor,
)

MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/VibeVoice-1.5B")
DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "en")
HF_TOKEN = os.getenv("HF_TOKEN", None)
SAMPLE_RATE = 16000

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[VibeVoice] Loading model '{MODEL_NAME}' on {device}...")
model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    token=HF_TOKEN,
).to(device)
model.eval()

processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_NAME, token=HF_TOKEN)
print("[VibeVoice] Model loaded.")


def decode_voice_prompt(voice_b64: str) -> np.ndarray:
    audio_bytes = base64.b64decode(voice_b64)
    buf = io.BytesIO(audio_bytes)
    waveform, sr = torchaudio.load(buf)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sr != SAMPLE_RATE:
        waveform = torchaudio.functional.resample(waveform, sr, SAMPLE_RATE)
    return waveform.squeeze(0).numpy()


def to_device(d, dev):
    return {
        k: v.to(dev) if isinstance(v, torch.Tensor) else v
        for k, v in d.items()
    }


def synthesize(text: str, language: str, voice_audio: np.ndarray = None) -> str:
    speech_kwargs = {}

    if voice_audio is not None:
        speech_inputs = processor.prepare_speech_inputs(
            [voice_audio],
            return_tensors="pt",
            device=device,
            dtype=torch.bfloat16,
        )
        speech_kwargs = to_device(speech_inputs, device)

    text_inputs = processor(text=text, return_tensors="pt")
    text_inputs = to_device(text_inputs, device)

    with torch.no_grad():
        output = model.generate(
            input_ids=text_inputs.get("input_ids"),
            attention_mask=text_inputs.get("attention_mask"),
            tts_text_ids=text_inputs.get("tts_text_ids"),
            speech_input_mask=text_inputs.get("speech_input_mask"),
            return_speech=True,
            language=language,
            **speech_kwargs,
        )

    if isinstance(output, tuple):
        audio = output[0]
    elif hasattr(output, "speech"):
        audio = output.speech
    elif hasattr(output, "sequences"):
        audio = output.sequences
    else:
        audio = output

    audio = audio.cpu().to(torch.float32)
    if audio.dim() == 1:
        audio = audio.unsqueeze(0)
    if audio.dim() == 3:
        audio = audio.squeeze(0)

    buf = io.BytesIO()
    torchaudio.save(buf, audio, SAMPLE_RATE, format="wav")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def handler(job):
    job_input = job.get("input", {})
    text = job_input.get("text")
    language = job_input.get("language", DEFAULT_LANGUAGE)
    voice_b64 = job_input.get("voice_prompt")

    if not isinstance(text, str) or not text.strip():
        return {"error": "Missing required 'text' (non-empty string)."}

    voice_audio = None
    if voice_b64:
        try:
            voice_audio = decode_voice_prompt(voice_b64)
        except Exception as e:
            return {"error": f"Failed to decode voice_prompt: {e}"}

    try:
        audio_b64 = synthesize(text.strip(), language, voice_audio)
        return {
            "language": language,
            "audio_base64": audio_b64,
            "voice_prompted": voice_b64 is not None,
        }
    except Exception as e:
        raise RuntimeError(f"Inference failed: {e}")


runpod.serverless.start({"handler": handler})
