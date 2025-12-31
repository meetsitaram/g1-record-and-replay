#!/bin/bash
# Setup script for g1-record-and-replay dependencies
# This follows the official unitree_sdk2_python installation instructions
# See: https://github.com/unitreerobotics/unitree_sdk2_python

set -e  # Exit on error

echo "====================================="
echo "G1 Record and Replay - Dependency Setup"
echo "====================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo -e "${RED}Error: Must run from g1-record-and-replay directory${NC}"
    exit 1
fi

# Step 1: Check for cyclonedds
echo -e "\n${YELLOW}Step 1: Checking for cyclonedds...${NC}"
if [ -d "$HOME/cyclonedds/install" ]; then
    echo -e "${GREEN}✓ cyclonedds already installed at ~/cyclonedds/install${NC}"
else
    echo -e "${YELLOW}cyclonedds not found. Installing...${NC}"
    echo -e "${YELLOW}Following official unitree_sdk2_python instructions...${NC}"
    
    # Official instructions from unitree_sdk2_python README
    cd ~
    git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
    cd cyclonedds && mkdir build install && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=../install
    cmake --build . --target install
    
    echo -e "${GREEN}✓ cyclonedds installed${NC}"
    cd - > /dev/null
fi

# Step 2: Set environment variable
echo -e "\n${YELLOW}Step 2: Setting CYCLONEDDS_HOME...${NC}"
export CYCLONEDDS_HOME="$HOME/cyclonedds/install"
echo -e "${GREEN}✓ CYCLONEDDS_HOME=$CYCLONEDDS_HOME${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Step 3: Install unitree SDK
echo -e "\n${YELLOW}Step 3: Installing unitree SDK...${NC}"
echo -e "${YELLOW}Following official unitree_sdk2_python instructions (using uv pip)...${NC}"
cd "$PROJECT_ROOT/unitree_sdk2_python"
source "$PROJECT_ROOT/g1-record-and-replay/.venv/bin/activate"
# Official uses: pip3 install -e .
# We use: uv pip install -e . (faster, same result)
CYCLONEDDS_HOME="$HOME/cyclonedds/install" uv pip install -e .
echo -e "${GREEN}✓ unitree SDK installed${NC}"

# Step 4: Install g1-record-and-replay
echo -e "\n${YELLOW}Step 4: Installing g1-record-and-replay...${NC}"
cd "$PROJECT_ROOT/g1-record-and-replay"
uv pip install -e .
echo -e "${GREEN}✓ g1-record-and-replay installed${NC}"

# Step 5: Test imports
echo -e "\n${YELLOW}Step 5: Testing imports...${NC}"
python -c "import unitree_sdk2py; print('✓ unitree_sdk2py imports OK')"
python -c "from g1_record_replay.core import DataManager; print('✓ g1_record_replay imports OK')"

echo -e "\n${GREEN}====================================="
echo "✓ Setup complete!"
echo "=====================================${NC}"
echo ""
echo "Add this to your ~/.bashrc or ~/.zshrc:"
echo "export CYCLONEDDS_HOME=\"$HOME/cyclonedds/install\""
echo ""
echo "Quick test:"
echo "  python tests/test_connection.py --network-interface eth0"

