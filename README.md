# Search a Group Chat Properly

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Sentence-Transformers](https://img.shields.io/badge/embeddings-MiniLM--L12--v2-orange.svg)](https://www.sbert.net/)
[![Benchmark Hit@3](https://img.shields.io/badge/Hit%403-100%25-brightgreen.svg)](scripts/run_benchmark.py)
[![Zero-Lexical Hit@3](https://img.shields.io/badge/Zero--Lexical%20Hit%403-100%25-brightgreen.svg)](scripts/run_benchmark.py)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](#copyright)

> **"When did we decide on Manali?"** You know the message exists. It is somewhere in four thousand messages, across six months, and you do not remember the exact words used — someone typed *"chalo Manali fix hai, pahadon me chalte hain"*, and searching for *"Manali"* returns 200 noisy results. Conventional Ctrl+F keyword search fails at the exact moment you need it most: when you have forgotten the wording but remember the meaning.

**Search a Group Chat Properly** is a production-grade, context-aware semantic search engine and conversational AI copilot built specifically for code-mixed **Hinglish** group chats (WhatsApp / Telegram / Slack).

---

## Table of Contents

- [The Problem with Group Chat Search](#the-problem-with-group-chat-search)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Security & Environment Variables](#security--environment-variables)
- [Quickstart Guide](#quickstart-guide)
- [Universal Setup Guide (Any Device)](#-universal-setup-guide-run-on-any-device)
  - [Windows 10 / 11](#-option-1-windows-10--11)
  - [macOS (Apple Silicon & Intel)](#-option-2-macos-intel--apple-silicon-m1m2m3m4)
  - [Linux (Ubuntu, Fedora, Arch)](#-option-3-linux-ubuntu--debian--fedora--arch)
  - [Docker (One-Command Run)](#-option-4-docker-containerized-run-anywhere)
  - [Mobile & Local Wi-Fi Sharing](#-option-5-wireless-local-wi-fi-sharing-test-on-mobile--tablet--lan)
  - [Troubleshooting & FAQ](#%EF%B8%8F-common-troubleshooting--faq)
- [Benchmark Suite & Accuracy](#benchmark-suite--accuracy)
- [REST API Reference](#rest-api-reference)
- [Corpus & Ground Truth Details](#corpus--ground-truth-details)
- [Project Directory Structure](#project-directory-structure)
- [Copyright](#copyright)

---

## The Problem with Group Chat Search

Standard text search in chat exports suffers from four structural flaws:

1. **Vocabulary Mismatch & Romanized Code-Mixing**: Indian group chats blend Hindi and English (*"kiraya chaunvan hazaar hai"*, *"hisab kitab excel sheet me"*, *"scorpio book kar li"*). English queries like *"monthly rent"* or *"manage shared finances"* have **zero lexical words in common** with the messages.
2. **Conversational Bursts**: Decisions don't happen in single isolated sentences. One user asks a question, another confirms, and a third reacts. Displaying a single message without surrounding conversation produces disjointed noise.
3. **Repeated Filler & Noise Flooding**: Narrow date or sender filters often pull in repetitive background chatter (*"sprint planning boring chal rahi hai"*, *"battery low h"*, *"ok"*, *"done"*) because there is no minimum semantic floor or duplicate penalty.
4. **Brittle Date & Speaker Queries**: Queries like *"what did Tanvi say about the broker in early July"* require simultaneous entity extraction, fuzzy temporal bounding, and dense semantic ranking.

---

## Key Features

- **Three Query Shapes Handled Automatically**:
  - **Semantic**: Concept-level matching (*"what was the agreed monthly apartment payment"* $\rightarrow$ `#1882`: *"kiraya chaunvan hazaar hai, teen logon me split hoga"*).
  - **Attributed**: Automatic speaker detection & filtering (*"what did Kabir specify about the trip budget ceiling"* $\rightarrow$ auto-routes to `Kabir Sharma` and retrieves `#1000`).
  - **Temporal**: Fuzzy natural-language calendar bounding (*"what hackathon ideas were proposed in early September"* $\rightarrow$ scopes to Aug 31 – Sep 10 and retrieves `#2979` & `#3012`).
- **Context Preservation**: Every search result surfaces the surrounding conversational window ($\pm 3$ to $\pm 7$ adjacent messages) rendered in WhatsApp-style directional bubbles.
- **Production-Grade Edge Case Handling**:
  - **Hard Semantic Floor** (`SEMANTIC_FLOOR = 0.12`): Prevents low-quality filler from ranking high inside date windows.
  - **Duplicate Boilerplate Suppression**: Penalizes repeated generic messages ($\ge 3$ occurrences in corpus) by `-0.35`.
  - **Colloquial Filler Dictionary**: Identifies and down-weights one-word acknowledgments (*"k"*, *"hmm"*, *"chalo"*, *"sahi"*, *"badhiya"*).
  - **Forwarded Message Demotion**: Distinguishes authentic group decisions from forwarded broadcasts.
- **Conversational Copilot (OpenRouter Integration - LLaMA 3.3 70B)**:
  - Powered by high-performing conversational LLMs (default: `meta-llama/llama-3.3-70b-instruct`).
  - Explains the **summary of the situation conversationally** in natural Hinglish/English rather than just listing citations.
  - Unpacks conversational nuances (rent negotiations, road trip planning, budget agreements) with embedded citations (e.g., `[#1882]`, `[#4189]`).
  - Gracefully falls back to deterministic local synthesis if no API key is provided.
- **Linear / WhatsApp Dark UI**: Fast, responsive dark web interface with suggestion chips, context drawer, markdown chat responses, and interactive benchmark scorecard.

---

## System Architecture

```
User Query: "What startup product are we building for the hackathon?"
                          │
                          ▼
            ┌───────────────────────────┐
            │   Query Intent Analyzer   │
            │  - Speaker Extraction     │
            │  - Fuzzy Temporal Parser  │
            └─────────────┬─────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌───────────────────┐           ┌───────────────────┐
│ Candidate Filters │           │ Dense Embedding   │
│ - Speaker Mask    │           │ MiniLM-L12-v2     │
│ - Date Bounds     │           │ 384-dim vector    │
└─────────┬─────────┘           └─────────┬─────────┘
          │                               │
          └───────────────┬───────────────┘
                          ▼
            ┌───────────────────────────┐
            │  Cosine Matrix Dot-Product│
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │  Hybrid Bonus & Penalties │
            │  + Concept Boost (+0.20)  │
            │  - Semantic Floor (<0.12) │
            │  - Frequency Penalty(>=3x)│
            │  - Filler Acknowledgment  │
            │  - Forwarded News Penalty │
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │ Ranked Results + Context  │
            │ (Burst slice: ±3 to ±7)   │
            └───────────────────────────┘
```

---

## Security & Environment Variables

> [!IMPORTANT]
> **API keys are NEVER committed to version control.** The project is pre-configured with a `.gitignore` that ignores all `.env` files and secrets.

### 1. Configure OpenRouter API Key

The application reads the OpenRouter API key from a `.env` file at the project root or from system environment variables.

Copy the example environment template:
```powershell
copy .env.example .env
```

Open `.env` in any text editor and add your key:
```bash
# .env (Excluded from Git via .gitignore)
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

*(You can obtain a free or pay-as-you-go key from [openrouter.ai/keys](https://openrouter.ai/keys).)*

### 2. Local Fallback Mode (Zero Configuration)
If no `OPENROUTER_API_KEY` is provided, the application runs in **Local Fallback Mode**:
- Semantic Search and the Benchmark Suite operate at 100% full capacity.
- The Chat Copilot uses a deterministic heuristic synthesizer that quotes the top messages with citations without calling external APIs.

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 2. Installation
Clone the repository:
```powershell
git clone https://github.com/sakshi-19165/group-chat-search.git
cd group-chat-search
```

Create a virtual environment (optional but recommended):
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:
```powershell
pip install -r requirements.txt
```

### 3. Embeddings & Index Initialization
The precomputed 384-dimensional embeddings matrix for all 4,250 messages is included (`engine/embeddings.npy`, ~6.2 MB). 

To regenerate the index from scratch at any time:
```powershell
python engine/build_index.py
```

### 4. Start the Application Server
Run the FastAPI web application:
```powershell
python server/app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

---

## 🚀 Universal Setup Guide (Run on Any Device)

Whether you are on Windows, macOS, Linux, using Docker, or want to test wirelessly from a smartphone on the same local Wi-Fi, follow the detailed instructions below.

---

### 💻 Option 1: Windows (10 / 11)

#### 1. Prerequisites
- **Python 3.10 to 3.12**: Download from [python.org](https://www.python.org/downloads/windows/).  
  *Important:* Check the box **"Add python.exe to PATH"** during setup.
- **Git**: Download from [git-scm.com](https://git-scm.com/).

#### 2. Clone the Repository
Open **PowerShell** (or Windows Terminal) and run:
```powershell
git clone https://github.com/sakshi-19165/group-chat-search.git
cd group-chat-search
```

#### 3. Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# If PowerShell blocks script execution, temporarily allow it for this process:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate the virtual environment:
.venv\Scripts\Activate.ps1
```
*(If using classic Command Prompt `cmd.exe`, run `.venv\Scripts\activate.bat` instead)*

#### 4. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configure Conversational AI (Optional)
The search engine works 100% locally with precomputed embeddings. To enable the articulate Conversational Copilot:
```powershell
copy .env.example .env
```
Open `.env` in Notepad and insert your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
```

#### 6. Start the Server
```powershell
python server/app.py
```
Visit `http://127.0.0.1:8000/` in your browser.

---

### 🍏 Option 2: macOS (Intel & Apple Silicon M1/M2/M3/M4)

#### 1. Prerequisites
Install [Homebrew](https://brew.sh/) if not already installed, then install Python 3.11 and Git:
```bash
brew install python@3.11 git
```

#### 2. Clone the Repository
```bash
git clone https://github.com/sakshi-19165/group-chat-search.git
cd group-chat-search
```

#### 3. Create & Activate Virtual Environment
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*(On Apple Silicon chips, PyTorch automatically takes advantage of Metal Performance Shaders MPS acceleration).*

#### 5. Configure Environment & Launch
```bash
cp .env.example .env
# Edit .env with your favorite editor (e.g. nano .env)
python server/app.py
```
Open `http://127.0.0.1:8000/` in Safari or Chrome.

---

### 🐧 Option 3: Linux (Ubuntu / Debian / Fedora / Arch)

#### 1. Install System Packages
**Debian / Ubuntu:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl
```

**Fedora / RedHat:**
```bash
sudo dnf install -y python3 python3-pip python3-virtualenv git curl
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip git curl
```

#### 2. Setup and Launch
```bash
git clone https://github.com/sakshi-19165/group-chat-search.git
cd group-chat-search

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python server/app.py
```
Open `http://127.0.0.1:8000/` in your browser.

---

### 🐳 Option 4: Docker (Containerized Run Anywhere)

If you have Docker Desktop or Docker Engine installed, you can launch the complete application with zero local Python setup:

#### 1. Build the Docker Image
```bash
docker build -t group-chat-search .
```

#### 2. Run the Container
```bash
# Option A: Run with local synthesized Copilot
docker run -d -p 8000:8000 --name chat-search group-chat-search

# Option B: Run with Conversational LLaMA 3.3 70B Copilot
docker run -d -p 8000:8000 \
  -e OPENROUTER_API_KEY="sk-or-v1-your-key-here" \
  -e OPENROUTER_MODEL="meta-llama/llama-3.3-70b-instruct" \
  --name chat-search group-chat-search
```

#### 3. View the Application
Navigate to `http://localhost:8000/`.

To inspect logs or stop:
```bash
docker logs -f chat-search
docker stop chat-search && docker rm chat-search
```

---

### 📱 Option 5: Wireless Local Wi-Fi Sharing (Test on Mobile / Tablet / LAN)

You can easily interact with the search engine from an iPhone, iPad, Android phone, or secondary laptop on the same local network:

#### 1. Start Server on All Network Interfaces
Run with `--host 0.0.0.0`:
```bash
python server/app.py --host 0.0.0.0 --port 8000
```

#### 2. Find Your Host Machine's Local IP Address
- **Windows**: Open PowerShell, run `ipconfig`, and find your `IPv4 Address` under your active Wi-Fi adapter (e.g., `192.168.1.45`).
- **macOS**: Go to *System Settings > Wi-Fi > Details*, or run `ipconfig getifaddr en0`.
- **Linux**: Run `hostname -I | awk '{print $1}'`.

#### 3. Connect from Mobile Browser
On your smartphone or tablet connected to the same Wi-Fi, open Safari or Chrome and navigate to:
```
http://<YOUR-LOCAL-IP>:8000
# Example: http://192.168.1.45:8000
```
*(If the page does not load, allow port 8000 or Python in your Windows Defender Firewall / OS Firewall settings).*

---

### 🛠️ Common Troubleshooting & FAQ

| Problem | Cause | Verified Solution |
| :--- | :--- | :--- |
| **`Scripts are disabled on this system`** | Windows PowerShell ExecutionPolicy default | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current terminal, then reactivate `.venv\Scripts\Activate.ps1`. |
| **`Address already in use: 8000`** | Another application or previous instance is running on port 8000 | Specify an alternate port: `python server/app.py --port 8080`, then open `http://127.0.0.1:8080/`. |
| **`No module named sentence_transformers`** | Virtual environment is not activated | Look for `(.venv)` in your terminal prompt. If absent, activate it via `.venv\Scripts\Activate.ps1` (Win) or `source .venv/bin/activate` (Mac/Linux). |
| **PyTorch download takes long** | Neural network dependency wheel size | Sentence-transformers installs PyTorch (~180MB). On slower connections, use `pip install --default-timeout=120 -r requirements.txt`. |
| **Do I need an OpenRouter API key?** | AI Copilot configuration | No. The app is 100% operational offline without any key. Semantic search, temporal bounding, and local synthesis work immediately. |
| **How to re-index custom chat data?** | Updating or replacing `dataset/messages.json` | Run `python engine/build_index.py`. It computes 384-dimensional embeddings and caches them into `engine/embeddings.npy` in ~15 seconds. |

---

## Benchmark Suite & Accuracy

The project includes an automated evaluation suite of **40 gold-standard benchmark queries** spanning all three query shapes, including 10 zero-lexical overlap tests.

### Scorecard Results

| Metric | Measured Score | Industry Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Hit@3 Accuracy (Top 3)** | **100.0% (40/40)** | $\ge 80\%$ | **PERFECT** |
| **Hit@5 Accuracy (Top 5)** | **100.0% (40/40)** | $\ge 90\%$ | **PERFECT** |
| **Zero-Lexical Overlap Hit@3** | **100.0% (10/10)** | $\ge 80\%$ | **PERFECT** |
| **Hit@1 Accuracy (Rank #1)** | **82.5% (33/40)** | $\ge 70\%$ | **PASS** |
| **Mean Reciprocal Rank (MRR)** | **0.908** | $\ge 0.80$ | **PASS** |
| **Search Latency (warm)** | **~25–45 ms** | $< 200	ext{ ms}$ | **SUB-50MS** |

### Running the CLI Benchmark
```powershell
python scripts/run_benchmark.py
```

### Running the UI Benchmark
Click on the **Benchmark Suite** tab in the web interface and click **"Run Evaluation Suite"** to view real-time latency graphs, pass/fail badges, and filterable tables.

---

## REST API Reference

### 1. `POST /api/search`
Executes semantic search over the corpus.
- **Request Body**:
  ```json
  {
    "query": "when was the vacation destination finalized?",
    "top_k": 5,
    "context_radius": 3
  }
  ```
- **Response**:
  ```json
  {
    "query_analysis": {
      "query_type": "semantic",
      "sender_filter": null,
      "date_start": null,
      "date_end": null
    },
    "results": [
      {
        "message": {
          "id": 840,
          "sender": "Kabir Sharma",
          "timestamp": "2024-06-04T23:08:00",
          "text": "chalo Manali fix hai, pahadon me chalte hain"
        },
        "score": 0.7621,
        "context": [...]
      }
    ],
    "total_candidates": 4250,
    "latency_ms": 32.4
  }
  ```

### 2. `GET /api/context/{message_id}`
Retrieves extended surrounding conversation burst for any message.
- **Query Parameters**: `radius` (default: 5)
- **Example**: `GET /api/context/840?radius=6`

### 3. `POST /api/chat`
Answers conversational queries with LLM synthesis and citations.
- **Request Body**:
  ```json
  {
    "query": "What is the monthly rent and deposit for the Indiranagar flat?",
    "top_k": 5
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The monthly rent is ₹54,000 split across 3 roommates [#1882], with an upfront security deposit of ₹2.5 Lakh [#1920].",
    "cited_messages": [...]
  }
  ```

### 4. `GET /api/benchmark`
Runs the 40-query test suite and returns precision metrics and per-query rankings.

### 5. `GET /api/stats`
Returns corpus summary (total messages, date range, message distribution per participant, and major decision thread overviews).

---

## Corpus & Ground Truth Details

The corpus simulates a realistic, messy group chat with **4,250 messages** spanning **6 months** (May 1 to October 31, 2024) across **8 participants**:

- **8 Realistic Personalities**: Kabir Sharma, Priya Patel, Rohan Mehta, Ananya Iyer, Vikram Malhotra, Tanvi Joshi, Arjun Nair, Sneha Rao.
- **3 Major Conversational Decision Arcs**:
  1. *Himachal Road Trip Planning (Manali)*: Dates locked June 14–18, Wooden cottage in Old Manali, Scorpio self-drive, ₹8,500 budget cap.
  2. *Indiranagar 3BHK Flat Hunting & Moving*: Ramesh broker, ₹54,000 monthly rent, ₹2.5L deposit, moving date August 1st.
  3. *ChatPulse Hackathon Project*: Semantic search tool idea, FastAPI + React + Postgres stack, Sept 25 deck deadline, 2nd place win in AI category.
- **Real-World Conversational Messiness**: Background noise, Swiggy food orders, memes, forwarded news, short replies, and typo-tolerant Hinglish code-mixing.

---

## Project Directory Structure

```
group-chat-search/
├── .env.example               # Template environment configuration
├── .gitignore                 # Security exclusion list (ignores .env, caches)
├── README.md                  # Comprehensive documentation
├── requirements.txt           # Python dependencies
├── dataset/
│   ├── benchmark_queries.json # 40 gold-standard queries (multi-target & proximity)
│   ├── chat_corpus.json       # 4,250 structured messages
│   ├── chat_export.txt        # Raw WhatsApp export format
│   └── generate_corpus.py     # Deterministic generator script (seed=42)
├── engine/
│   ├── build_index.py         # Embedding generation pipeline
│   ├── embeddings.npy         # 4,250 × 384 dense float32 vectors (~6.2 MB)
│   ├── index_metadata.json    # Index metadata & model reference
│   ├── normalizer.py          # Hinglish concept & synonym dictionary
│   └── search.py              # Semantic search engine with edge-case handling
├── server/
│   └── app.py                 # FastAPI backend with REST endpoints & static server
├── web/
│   ├── app.js                 # UI interactions, chat copilot, context drawer
│   ├── index.html             # WhatsApp-style dark theme interface
│   └── style.css              # Glassmorphism, tokens, responsive layout
└── scripts/
    ├── benchmark_results.json # Last evaluated benchmark JSON output
    └── run_benchmark.py       # Standalone CLI evaluation runner
```

---

## Copyright

© 2026 All rights reserved. This software is proprietary and confidential.
Unauthorized copying, distribution, or modification is strictly prohibited.
