# ---- CUDA 12.6 (provides cublas64_12.dll etc.) ----
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin;" + $env:PATH

# ---- CUDA 13.1 (provides cublasLt64_13.dll) ----
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\x64;" + $env:PATH

# ---- cuDNN (DLLs) ----
$env:PATH = "C:\Program Files\NVIDIA\CUDNN\v9.17\bin\13.1;" + $env:PATH

# ---- Whisper GPU config ----
$env:WHISPER_DEVICE="cuda"
$env:WHISPER_MODEL="medium"
$env:WHISPER_COMPUTE_TYPE="float16"

python -m uvicorn server_v2:app --reload --host 0.0.0.0 --port 8000
