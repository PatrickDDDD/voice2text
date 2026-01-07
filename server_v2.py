import os
import uuid
import shutil
import subprocess
import logging

from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel

# -----------------------------
# Basic config
# -----------------------------
APP_NAME = "stt-api"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(APP_NAME)

app = FastAPI(title=APP_NAME)

# CORS: allow front-end testing (tighten when deploying)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# FFmpeg helpers
# -----------------------------
# Optional: allow specifying explicit ffmpeg path to avoid PATH issues (Windows/VSCode)
# Example (PowerShell):
#   $env:FFMPEG_BIN="C:\ffmpeg\bin\ffmpeg.exe"
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "").strip()

def find_ffmpeg() -> str:
    """Return ffmpeg executable path or raise."""
    if FFMPEG_BIN and os.path.exists(FFMPEG_BIN):
        return FFMPEG_BIN
    p = shutil.which("ffmpeg")
    if p:
        return p
    raise RuntimeError("ffmpeg not found. Set FFMPEG_BIN or add ffmpeg to PATH.")

def to_wav_16k_mono(input_path: str, output_path: str):
    ffmpeg = find_ffmpeg()
    cmd = [ffmpeg, "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# -----------------------------
# GPU auto-detect + model config
# -----------------------------
def has_nvidia_gpu() -> bool:
    """Detect NVIDIA GPU availability via nvidia-smi."""
    nvsmi = shutil.which("nvidia-smi")
    if not nvsmi:
        return False
    try:
        # If nvidia-smi runs successfully, we assume CUDA device is available
        subprocess.run([nvsmi], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

# Environment overrides (highest priority)
ENV_MODEL = os.environ.get("WHISPER_MODEL", "").strip()
ENV_DEVICE = os.environ.get("WHISPER_DEVICE", "").strip()
ENV_COMPUTE = os.environ.get("WHISPER_COMPUTE_TYPE", "").strip()

# Decide device
if ENV_DEVICE:
    DEVICE = ENV_DEVICE
else:
    DEVICE = "cuda" if has_nvidia_gpu() else "cpu"

# Decide model
if ENV_MODEL:
    MODEL_SIZE = ENV_MODEL
else:
    # Good defaults for "voice question to assistant"
    # MODEL_SIZE = "large-v3" if DEVICE == "cuda" else "medium"
    MODEL_SIZE = "medium" if DEVICE == "cuda" else "small"

# Decide compute type
if ENV_COMPUTE:
    COMPUTE_TYPE = ENV_COMPUTE
else:
    COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

logger.info(f"Whisper config => model={MODEL_SIZE}, device={DEVICE}, compute_type={COMPUTE_TYPE}")
logger.info("Loading model... (first time may download model files)")

model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

logger.info("Model loaded successfully.")

# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    ffmpeg_ok = True
    ffmpeg_path = None
    try:
        ffmpeg_path = find_ffmpeg()
    except Exception:
        ffmpeg_ok = False

    return {
        "ok": True,
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "ffmpeg_ok": ffmpeg_ok,
        "ffmpeg": ffmpeg_path,
    }

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Query("zh", description="Language code: zh/en/auto"),
    vad: bool = Query(True, description="Enable VAD filter for more stable results"),
    timestamps: bool = Query(False, description="Return segment timestamps"),
    beam_size: int = Query(5, description="Beam search size (higher=more accurate, slower)"),
):
    """
    Upload an audio file and get transcription text.
    Input formats: wav/mp3/m4a/webm/... (ffmpeg required for non-wav)
    """
    suffix = os.path.splitext(file.filename or "")[1] or ".bin"
    uid = str(uuid.uuid4())
    raw_path = os.path.join(UPLOAD_DIR, f"{uid}{suffix}")
    wav_path = os.path.join(UPLOAD_DIR, f"{uid}.wav")

    # Save uploaded file
    with open(raw_path, "wb") as f:
        f.write(await file.read())

    # Convert to wav 16k mono
    try:
        to_wav_16k_mono(raw_path, wav_path)
    except Exception as e:
        # Keep consistent JSON format (HTTP 200 but ok=false)
        return {"ok": False, "error": f"Audio conversion failed: {repr(e)}"}

    # Transcribe
    try:
        lang = None if language in ("auto", "", None) else language

        segments, info = model.transcribe(
            wav_path,
            language=lang,
            vad_filter=vad,
            beam_size=beam_size,
            # better for short "voice questions" to assistant:
            condition_on_previous_text=False,
        )

        text_parts = []
        segs = []
        for seg in segments:
            text_parts.append(seg.text)
            if timestamps:
                segs.append({"start": seg.start, "end": seg.end, "text": seg.text})

        result_text = "".join(text_parts).strip()

        resp = {
            "ok": True,
            "text": result_text,
            "language": info.language,
            "duration": info.duration,
            "model": MODEL_SIZE,
            "device": DEVICE,
        }
        if timestamps:
            resp["segments"] = segs
        return resp

    finally:
        # Clean temp files
        for p in (raw_path, wav_path):
            try:
                os.remove(p)
            except Exception:
                pass
