# CSE476 Final Project

This repository contains our modular inference-time agent. Built with [LangChain](https://docs.langchain.com/).

## Current Structure
- batch answer generator (entry point): `src/generate_answers.py`
- shared model/env client: `src/agent/client.py`
- strategy router: `src/agent/router.py`
- strategy implementations: `src/agent/graphs/`
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
- `LLM_API_KEY` (required)
- `BASE_URL`
- `MODEL_NAME`
- `TEMPERATURE`

> Note: input and output paths to .json files are set in `src/generate_answers.py`. Configure as needed. 

## Run
from project root:
```bash
generate-answers
```
OR from `src/`:
```bash
python generate_answers.py
```

## Add New Inference Techniques (graphs)
1. add a new class under `src/agent/graphs/` (example: `cot.py`).
2. use the `BaseGraph` interface (see `direct.py` for example).
3. register it in `src/agent/router.py` inside `REGISTRY`.

## TODO
- implement remaining strats
- config options for strats (config class)
- guardrails and validation (api calls < 20, response length, etc.)
- evaluation framework (optional)
