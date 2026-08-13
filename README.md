# Eikon VibeVoice Worker

RunPod serverless worker for [microsoft/VibeVoice-1.5B](https://github.com/microsoft/VibeVoice) with voice prompt (voice cloning) support.

Based on [jords1755/VibeVoice](https://github.com/jords1755/VibeVoice) community worker, extended with `voice_prompt` parameter for consistent narrator voice across episodes.

## API

### Input

```json
{
  "input": {
    "text": "Your narration text here...",
    "language": "en",
    "voice_prompt": "<base64-encoded WAV audio — 10-30 seconds of reference voice>"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to synthesize |
| `language` | string | No | `"en"` (default) or `"zh"` |
| `voice_prompt` | string | No | Base64-encoded WAV of reference voice. Omit for default voice. |

### Output

```json
{
  "language": "en",
  "audio_base64": "<base64-encoded WAV at 16kHz>",
  "voice_prompted": true
}
```

## Voice Prompt Guidelines

- **Format:** WAV, mono, 16kHz preferred (auto-resampled if different)
- **Length:** 10-30 seconds of clean speech (no music, no background noise)
- **Content:** Natural speaking — the model learns pitch, warmth, cadence, and pacing
- **Consistency:** Use the same reference clip across all episodes for a consistent narrator voice

## Setup

### 1. Push to GitHub

```bash
gh repo create eikon-vibevoice-worker --public --source=. --push
```

### 2. Wait for GitHub Actions

The workflow builds the Docker image and pushes to `ghcr.io/<username>/eikon-vibevoice-worker:latest`.

Make the package public: GitHub → Packages → eikon-vibevoice-worker → Package settings → Change visibility → Public.

### 3. Deploy on RunPod

Create a serverless endpoint using the image from GHCR:
- GPU: RTX 4090
- Min workers: 0 (pay only when running)
- Max workers: 1
- Container disk: 20 GB

## Cost

RTX 4090 serverless: $0.34/hr ($0.00034/sec). You only pay for active inference time.
