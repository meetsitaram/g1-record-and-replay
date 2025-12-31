
import time
import sys
import threading
import os
import requests
import json
from datetime import datetime, timezone # Added for time handling
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize

# --- Configuration ---
SERVER_URL = "http://52.37.4.82:3001/robot"
ROBOT_NAME = "unitree_g1_robot3"
UPDATE_INTERVAL = 5

# --- Import G1 Messages ---
try:
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
    try:
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import BmsState_
        BMS_AVAILABLE = True
    except ImportError:
        BMS_AVAILABLE = False
        print("[Info] BmsState_ not found. Using voltage fallback.")
except ImportError:
    print("Error: Could not import 'unitree_hg'. Update unitree_sdk2py.")
    sys.exit(1)

# --- Global Data ---
latest_low_state = None
latest_bms_state = None
lock = threading.Lock()

# --- Callbacks ---
def LowStateHandler(msg: LowState_):
    global latest_low_state
    with lock:
        latest_low_state = msg

def BmsStateHandler(msg):
    global latest_bms_state
    with lock:
        latest_bms_state = msg

# --- Helpers ---
def estimate_battery_from_voltage(vol):
    min_v, max_v = 42.0, 54.0
    pct = (vol - min_v) / (max_v - min_v) * 100
    return max(0, min(100, pct))

def get_serial_number():
    try:
        if os.path.exists("/etc/unitree/serial"):
            with open("/etc/unitree/serial", "r") as f:
                return f.read().strip()
    except: pass
    return "Unknown"

# --- Main Logic ---
def process_and_upload(serial_num):
    # 1. Thread-safe data copy
    with lock:
        state = latest_low_state
        bms = latest_bms_state

    if state is None:
        print("Waiting for robot data...")
        return

    # 2. Process Battery
    if bms is not None:
        batt_pct = float(bms.soc)
        batt_vol = float(bms.voltage)
    elif state.motor_state and len(state.motor_state) > 0:
        batt_vol = float(state.motor_state[0].vol)
        batt_pct = estimate_battery_from_voltage(batt_vol)
    else:
        batt_pct = 0.0
        batt_vol = 0.0

    # 3. Process Joints
    joint_names = [
        "L_Hip_Roll", "L_Hip_Yaw", "L_Hip_Pitch", "L_Knee", "L_Ankle_Pitch", "L_Ankle_Roll",
        "R_Hip_Roll", "R_Hip_Yaw", "R_Hip_Pitch", "R_Knee", "R_Ankle_Pitch", "R_Ankle_Roll",
        "Waist_Yaw", "Waist_Roll", "Waist_Pitch",
        "L_Sho_Pitch", "L_Sho_Roll", "L_Sho_Yaw", "L_Elbow",
        "R_Sho_Pitch", "R_Sho_Roll", "R_Sho_Yaw", "R_Elbow"
    ]

    joints_payload = {}
    temperatures_payload = {}
    max_temp = 0.0
    
    for i, motor in enumerate(state.motor_state):
        if i >= 40: break

        if i < len(joint_names):
            name = joint_names[i]
        elif i >= 23 and i <= 34:
            name = f"Hand_J{i}"
        else:
            name = f"Aux_J{i}"

        # Handle list vs float temperature
        raw_temp = motor.temperature
        if isinstance(raw_temp, list) or hasattr(raw_temp, '__len__'):
            t_val = float(raw_temp[0]) if len(raw_temp) > 0 else 0.0
        else:
            t_val = float(raw_temp)
        
        if t_val > max_temp: max_temp = t_val

        if i < 23 or t_val > 0:
            joints_payload[name] = round(float(motor.q), 4)
            temperatures_payload[name] = round(t_val, 1)

    # 4. Construct JSON Payload (With UTC Time)
    # Python dictionaries maintain insertion order (Python 3.7+)
    payload = {
        "name": ROBOT_NAME,
        "last_update": datetime.now(timezone.utc).isoformat(), # Current UTC Time
        "serial": serial_num,
        "battery": {
            "percentage": round(batt_pct, 1),
            "voltage": round(batt_vol, 2)
        },
        "joints": joints_payload,
        "temperatures": temperatures_payload,
        "peak_temp": round(max_temp, 1)
    }

    # 5. Print Summary
    print("\033[H\033[J", end="") 
    print("=" * 60)
    print(f"G1 UPLOAD CLIENT | Target: {SERVER_URL}")
    print(f"Time: {payload['last_update']} | Battery: {batt_pct:.1f}%")
    print("-" * 60)
    
    # 6. Upload
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=4)
        print(f"Upload Status: {response.status_code}")
        print(f"Server Reply: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Upload Error: {e}")
    
    print("-" * 60)
    print(f"Payload Size: {len(json.dumps(payload))} bytes. Waiting 5s...")

def main():
    if len(sys.argv) < 2:
        network_interface = "eth0"
    else:
        network_interface = sys.argv[1]

    print(f"Initializing on: {network_interface}")
    try:
        ChannelFactoryInitialize(0, network_interface)
    except Exception as e:
        print(f"Init Failed: {e}")
        sys.exit(1)

    sub_low = ChannelSubscriber("rt/lowstate", LowState_)
    sub_low.Init(LowStateHandler, 10)

    if BMS_AVAILABLE:
        sub_bms = ChannelSubscriber("rt/bms/state", BmsState_)
        sub_bms.Init(BmsStateHandler, 10)

    serial_num = get_serial_number()
    print("Connected. Starting upload loop...")

    try:
        while True:
            time.sleep(UPDATE_INTERVAL)
            process_and_upload(serial_num)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == '__main__':
    main()
