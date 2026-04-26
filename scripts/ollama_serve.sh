#!/bin/bash
# Starts the Ollama server on a GPU node using the Sol module.
# Usage: bash scripts/ollama_serve.sh

PORT=11434

module load ollama/0.9.0

export OLLAMA_MODELS=/scratch/${USER}/ollama_models
export OLLAMA_HOST="0.0.0.0:$PORT"

echo "GPU check:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || { echo "ERROR: no GPU visible"; exit 1; }
echo ""

ollama serve &
OLLAMA_PID=$!

# Wait for server to be ready
echo "Waiting for server..."
for i in {1..15}; do
    ollama list &>/dev/null && break
    sleep 1
done

# write connection info
cat > /scratch/${USER}/vllm_server_info.txt <<EOF
BASE_URL=http://$(hostname):$PORT
EOF

echo "==> Server running. Connection info:"
cat /scratch/${USER}/vllm_server_info.txt
echo ""
echo "Stop with: kill $OLLAMA_PID  (or Ctrl-C)"

wait
