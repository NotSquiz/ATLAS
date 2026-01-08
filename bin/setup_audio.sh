#!/bin/bash
# ATLAS Audio Setup for WSL2
# Run this script with sudo: sudo bash ~/ATLAS/bin/setup_audio.sh

set -e

echo "=== ATLAS Audio Setup for WSL2 ==="
echo ""

# Step 1: Install audio packages
echo "[1/5] Installing PulseAudio and ALSA..."
apt-get update
apt-get install -y pulseaudio pulseaudio-utils alsa-utils

# Step 2: Install Python audio libraries
echo ""
echo "[2/5] Installing Python audio libraries..."
pip3 install sounddevice soundfile numpy

# Step 3: Get Windows host IP (for PulseAudio connection)
echo ""
echo "[3/5] Detecting Windows host IP..."
WIN_HOST=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo "Windows host IP: $WIN_HOST"

# Step 4: Configure PulseAudio client
echo ""
echo "[4/5] Configuring PulseAudio client..."
mkdir -p ~/.config/pulse
cat > ~/.config/pulse/default.pa << EOF
# ATLAS PulseAudio config for WSL2
# Connect to Windows PulseAudio server
load-module module-native-protocol-tcp auth-ip-acl=$WIN_HOST
EOF

# Step 5: Create PULSE_SERVER env setup
echo ""
echo "[5/5] Creating environment setup..."
PULSE_EXPORT="export PULSE_SERVER=tcp:$WIN_HOST"

# Add to .bashrc if not already present
if ! grep -q "PULSE_SERVER" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# ATLAS Audio - PulseAudio for WSL2" >> ~/.bashrc
    echo "$PULSE_EXPORT" >> ~/.bashrc
    echo "Added PULSE_SERVER to ~/.bashrc"
else
    echo "PULSE_SERVER already in ~/.bashrc"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "IMPORTANT: You also need to install PulseAudio on Windows!"
echo ""
echo "Windows Setup Instructions:"
echo "1. Download PulseAudio for Windows: https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/"
echo "   Or use: scoop install pulseaudio"
echo ""
echo "2. Edit the PulseAudio config (usually in C:\\Users\\<user>\\scoop\\apps\\pulseaudio\\current\\etc\\pulse\\default.pa):"
echo "   Add this line: load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1;172.16.0.0/12"
echo ""
echo "3. Edit C:\\Users\\<user>\\scoop\\apps\\pulseaudio\\current\\etc\\pulse\\daemon.conf:"
echo "   Set: exit-idle-time = -1"
echo ""
echo "4. Run PulseAudio on Windows: pulseaudio.exe -D"
echo ""
echo "Then in WSL2, run: source ~/.bashrc"
echo "And test with: pactl info"
