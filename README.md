# CSE476 Final Project

This repository contains our modular inference-time agent.

## Current Structure
- batch answer generator (entry point): `src/generate_answers.py`
- agent loop: `src/agent/graph.py`
- tool definitions: `src/agent/tools.py`
- data: `data/` (input and output .json files)

## Setup
1. create and activate a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
2. install the project in editable mode:
```bash
python -m pip install -e .
```
3. create `.env` from `.env.example` and set values:
- `OPENAI_API_KEY` (or `LLM_API_KEY`) (required)
- `API_BASE` (or `BASE_URL`) (optional)
- `MODEL_NAME`
- `TEMPERATURE`

> Note: input and output paths to .json files are set in `src/generate_answers.py`. Configure as needed. 

## Run
from project root:
```bash
generate-answers
```
OR without installing (from project root):
```bash
python src/generate_answers.py
```

## Add New Inference Techniques
implement inference-time techniques in `src/agent/graph.py` (the `invoke_agent()` entrypoint).

define tools in `src/agent/tools.py` and call them from the agent implementation as needed.

## TODO
- implement remaining strats
- config options for strats (config class)
- guardrails and validation (api calls < 20, response length, etc.)
