🎙️ Whisper GPU Speech-to-Text API (Windows)

基于 **FastAPI + faster-whisper + CUDA GPU** 的本地语音转文字服务，
支持 Web 端录音测试，也可作为 **统一语音转文字 API** 供其他系统调用。

---

## ✨ 功能特性

* ✅ Whisper **GPU 加速**（NVIDIA RTX / CUDA）
* ✅ 支持中文 / 英文 / 自动语言识别
* ✅ 支持 VAD（静音过滤）
* ✅ 支持 Web 前端录音测试
* ✅ REST API 形式，方便后续接入智能助手 / LLM
* ✅ Windows 本地开发友好（无需 Docker）

---

## 📂 项目结构

```text
voice2text/
├── server_v2.py        # FastAPI 后端服务（Whisper API）
├── start_gpu.ps1       # GPU 启动脚本（关键）
├── test.html           # Web 端录音测试页面
├── uploads/            # 临时音频目录（自动生成）
├── README.md           # 本说明文件
```

---

## 🧱 环境要求

### 硬件

* NVIDIA GPU（推荐 ≥ 8GB 显存）
* 本项目测试环境：**RTX 3070**

### 操作系统

* Windows 10 / Windows 11（x64）

### 软件依赖

* Python **3.10+**
* NVIDIA Driver（支持 CUDA 12 / 13）
* CUDA Toolkit：

  * ✅ **CUDA 12.6**（必须）
  * ✅ CUDA 13.1（可并存）
* cuDNN **9.x**

---

## 📦 Python 依赖

建议使用虚拟环境：

```powershell
pip install fastapi uvicorn faster-whisper ctranslate2 python-multipart
```

---

## 🚀 启动方式（GPU）

### 1️⃣ 使用 `start_gpu.ps1`（推荐）

项目根目录执行：

```powershell
.\start_gpu.ps1
```

该脚本会：

* 注入 CUDA 12 / CUDA 13 / cuDNN 到当前进程 PATH
* 设置 Whisper GPU 参数
* 启动 FastAPI 服务

### `start_gpu.ps1` 内容说明

```powershell
# CUDA 12 runtime（ctranslate2 依赖）
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin;" + $env:PATH

# CUDA 13 runtime（cublasLt 依赖）
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\x64;" + $env:PATH

# cuDNN
$env:PATH = "C:\Program Files\NVIDIA\CUDNN\v9.17\bin\13.1;" + $env:PATH

# Whisper GPU 配置
$env:WHISPER_DEVICE="cuda"
$env:WHISPER_MODEL="medium"      # 可改为 large-v3
$env:WHISPER_COMPUTE_TYPE="float16"

python -m uvicorn server_v2:app --reload --host 0.0.0.0 --port 8000
```

> ⚠️ 该脚本只影响当前 PowerShell 进程，不污染系统 PATH（推荐做法）

---

## 🔍 服务验证

### 查看接口文档

浏览器访问：

```
http://localhost:8000/docs
```

### 健康检查

```http
GET /health
```

返回示例：

```json
{
  "ok": true,
  "model": "medium",
  "device": "cuda",
  "compute_type": "float16"
}
```

---

## 🎧 Web 端测试（录音）

直接用浏览器打开：

```
test.html
```

流程：

1. 点击「开始录音」
2. 说话
3. 停止录音
4. 上传转写
5. 返回识别文本

---

## 🔌 API 使用示例

### 接口

```http
POST /transcribe
```

### 参数

| 参数         | 类型    | 说明                     |
| ---------- | ----- | ---------------------- |
| file       | audio | 音频文件（webm / wav / mp3） |
| language   | query | zh / en / auto         |
| vad        | query | 是否启用 VAD               |
| timestamps | query | 是否返回时间戳                |

### 示例（curl）

```bash
curl -X POST "http://localhost:8000/transcribe?language=zh&vad=true" \
  -F "file=@test.wav"
```

---

## ⚙️ 模型配置建议

| 模型       | 精度    | 速度   | 适用场景      |
| -------- | ----- | ---- | --------- |
| small    | ⭐⭐    | ⭐⭐⭐⭐ | 快速测试      |
| medium   | ⭐⭐⭐⭐  | ⭐⭐⭐  | 默认推荐      |
| large-v3 | ⭐⭐⭐⭐⭐ | ⭐⭐   | 会议 / 专业场景 |

切换方式：

```powershell
$env:WHISPER_MODEL="large-v3"
```

---

## 🧠 工程说明（重要）

* Windows 下 **CUDA 12 + 13 + cuDNN** 允许并存
* `ctranslate2` 在 Windows 上依赖 **CUDA 12**
* Whisper GPU 调试成功后，生产环境推荐：

  * Linux + Docker + GPU
  * 或 CPU Whisper + GPU LLM

---

## 📌 常见问题

### Q: 为什么不用系统 PATH？

A: 避免 CUDA / cuDNN 污染系统环境，进程级注入更安全。

### Q: 支持实时语音吗？

A: 当前是 **录音后转写**；可扩展为 WebSocket / Streaming（后续可加）。

---

## 📜 License

Internal / Demo / Research Use


