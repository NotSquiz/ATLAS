#!/bin/bash
# ATLAS Ollama Installation Script
# Run with: sudo bash scripts/install_ollama.sh

set -e

echo "========================================"
echo "ATLAS Ollama Setup"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo bash scripts/install_ollama.sh"
    exit 1
fi

# Install Ollama
echo ""
echo "[1/4] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Add environment variables to user's bashrc
USER_HOME=$(eval echo ~$SUDO_USER)
BASHRC="$USER_HOME/.bashrc"

echo ""
echo "[2/4] Adding Ollama environment variables to $BASHRC..."

# Check if already added
if ! grep -q "OLLAMA_FLASH_ATTENTION" "$BASHRC"; then
    cat >> "$BASHRC" << 'EOF'

# ATLAS Ollama optimizations
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_MAX_LOADED_MODELS=1
EOF
    echo "  Environment variables added"
else
    echo "  Environment variables already present"
fi

# Create ATLAS Modelfile
echo ""
echo "[3/4] Creating ATLAS Modelfile..."
cat > "$USER_HOME/ATLAS-Modelfile" << 'EOF'
FROM qwen3:4b
PARAMETER num_ctx 4096
PARAMETER num_gpu 99
PARAMETER temperature 0.7
PARAMETER top_p 0.8
SYSTEM "You are ATLAS, a personal life assistant. Respond concisely for voice output. Use /no_think for simple queries."
EOF
chown $SUDO_USER:$SUDO_USER "$USER_HOME/ATLAS-Modelfile"
echo "  Created $USER_HOME/ATLAS-Modelfile"

echo ""
echo "[4/4] Starting Ollama service..."
systemctl enable ollama || true
systemctl start ollama || true

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "NEXT STEPS (run as your normal user):"
echo ""
echo "  1. Source bashrc to load environment variables:"
echo "     source ~/.bashrc"
echo ""
echo "  2. Pull the Qwen3-4B model (~2.5GB download):"
echo "     ollama pull qwen3:4b"
echo ""
echo "  3. Create the atlas-local model:"
echo "     ollama create atlas-local -f ~/ATLAS-Modelfile"
echo ""
echo "  4. Test it:"
echo "     ollama run atlas-local 'What is 2+2?'"
echo ""
echo "  5. Run the benchmark:"
echo "     cd ~/ATLAS && ./venv/bin/python scripts/test_ollama.py"
echo ""
