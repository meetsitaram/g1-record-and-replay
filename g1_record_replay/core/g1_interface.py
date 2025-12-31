"""G1 Robot Interface - Low-level SDK wrapper for motor control"""

from __future__ import annotations
import time
import numpy as np
from typing import Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

# Import SDK types for type checking only
if TYPE_CHECKING:
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

# Runtime imports with error handling
try:
    from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
    from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
    from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_ as LowState_Runtime
    from unitree_sdk2py.utils.crc import CRC
    from unitree_sdk2py.utils.thread import RecurrentThread
    from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
    SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Failed to import unitree_sdk2py: {e}")
    print("Some functionality may not work. Make sure unitree_sdk2py is installed.")
    SDK_AVAILABLE = False
    # Create dummy classes for when SDK is not available
    LowState_Runtime = None


G1_NUM_MOTOR = 29


class G1JointIndex:
    """Joint indices for G1 robot (29 DOF)"""
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleB = 4
    LeftAnkleRoll = 5
    LeftAnkleA = 5
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleB = 10
    RightAnkleRoll = 11
    RightAnkleA = 11
    WaistYaw = 12
    WaistRoll = 13
    WaistA = 13
    WaistPitch = 14
    WaistB = 14
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20
    LeftWristYaw = 21
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27
    RightWristYaw = 28


# Human-readable joint names
JOINT_NAMES = [
    "left_hip_pitch",
    "left_hip_roll",
    "left_hip_yaw",
    "left_knee",
    "left_ankle_pitch",
    "left_ankle_roll",
    "right_hip_pitch",
    "right_hip_roll",
    "right_hip_yaw",
    "right_knee",
    "right_ankle_pitch",
    "right_ankle_roll",
    "waist_yaw",
    "waist_roll",
    "waist_pitch",
    "left_shoulder_pitch",
    "left_shoulder_roll",
    "left_shoulder_yaw",
    "left_elbow",
    "left_wrist_roll",
    "left_wrist_pitch",
    "left_wrist_yaw",
    "right_shoulder_pitch",
    "right_shoulder_roll",
    "right_shoulder_yaw",
    "right_elbow",
    "right_wrist_roll",
    "right_wrist_pitch",
    "right_wrist_yaw",
]

# Joint group definitions
JOINT_GROUPS = {
    "legs": list(range(0, 12)),  # indices 0-11
    "waist": list(range(12, 15)),  # indices 12-14
    "arms": list(range(15, 29)),  # indices 15-28
    "all": list(range(29))
}


def get_joint_indices(group: str = "all") -> list:
    """
    Get joint indices for a specified group.
    
    Args:
        group: Joint group name ('arms', 'legs', 'waist', 'all')
        
    Returns:
        List of joint indices
    """
    if group not in JOINT_GROUPS:
        raise ValueError(f"Invalid joint group: {group}. Choose from {list(JOINT_GROUPS.keys())}")
    return JOINT_GROUPS[group]


# Default control gains
DEFAULT_KP = [
    60, 60, 60, 100, 40, 40,      # legs
    60, 60, 60, 100, 40, 40,      # legs
    60, 40, 40,                   # waist
    40, 40, 40, 40, 40, 40, 40,   # left arm
    40, 40, 40, 40, 40, 40, 40    # right arm
]

DEFAULT_KD = [
    1, 1, 1, 2, 1, 1,     # legs
    1, 1, 1, 2, 1, 1,     # legs
    1, 1, 1,              # waist
    1, 1, 1, 1, 1, 1, 1,  # left arm
    1, 1, 1, 1, 1, 1, 1   # right arm 
]


class Mode:
    """Motor control modes"""
    PR = 0  # Series Control for Pitch/Roll Joints
    AB = 1  # Parallel Control for A/B Joints


@dataclass
class JointState:
    """Joint state data"""
    positions: np.ndarray  # (29,) joint positions in radians
    velocities: np.ndarray  # (29,) joint velocities in rad/s
    torques: np.ndarray  # (29,) joint torques
    timestamp: float  # timestamp in seconds


class G1Interface:
    """
    High-level interface for G1 robot motor control.
    Handles low-level SDK communication and provides clean API.
    """
    
    def __init__(self, network_interface: Optional[str] = None, use_motion_switcher: bool = False):
        """
        Initialize G1 interface.
        
        Args:
            network_interface: Network interface name (e.g., 'enp2s0', 'eth0'). 
                             If None, uses default.
            use_motion_switcher: Whether to use MotionSwitcherClient (needed for active control)
        """
        self.network_interface = network_interface
        self.use_motion_switcher = use_motion_switcher
        self.num_motors = G1_NUM_MOTOR
        self.control_dt = 0.002  # 2ms
        
        # State
        self.low_state: Optional['LowState_'] = None
        self.low_cmd = None
        self.mode_machine = 0
        self.update_mode_machine = False
        self.is_initialized = False
        self.is_control_active = False
        
        # SDK objects
        self.msc = None
        self.lowcmd_publisher = None
        self.lowstate_subscriber = None
        self.control_thread = None
        self.crc = None
        
    def initialize(self):
        """Initialize SDK connection and channels"""
        print(f"Initializing G1 interface...")
        if self.network_interface:
            print(f"Network interface: {self.network_interface}")
        
        # Initialize channel factory (similar to g1_upload.py)
        try:
            if self.network_interface:
                ChannelFactoryInitialize(0, self.network_interface)
            else:
                ChannelFactoryInitialize(0)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize channel factory: {e}")
        
        # Only use motion switcher if we need to control the robot
        if self.use_motion_switcher:
            print("Initializing motion switcher for robot control...")
            self.msc = MotionSwitcherClient()
            self.msc.SetTimeout(5.0)
            self.msc.Init()
            
            # Release any existing control mode
            status, result = self.msc.CheckMode()
            while result.get('name'):
                print(f"Releasing existing mode: {result.get('name')}")
                self.msc.ReleaseMode()
                status, result = self.msc.CheckMode()
                time.sleep(1)
            
            # Create publisher for commands
            self.lowcmd_publisher = ChannelPublisher("rt/lowcmd", LowCmd_)
            self.lowcmd_publisher.Init()
            
            # Initialize CRC
            self.crc = CRC()
            
            # Initialize command message
            self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        
        # Create subscriber for state (always needed)
        self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_Runtime)
        self.lowstate_subscriber.Init(self._low_state_handler, 10)
        
        # Wait for first state message
        print("Waiting for robot state...")
        timeout = 10.0
        start_time = time.time()
        while self.low_state is None:
            if time.time() - start_time > timeout:
                raise TimeoutError("Failed to receive robot state within timeout")
            time.sleep(0.1)
            
        self.is_initialized = True
        if self.use_motion_switcher:
            print(f"G1 interface initialized successfully. Mode: {self.mode_machine}")
        else:
            print("G1 interface initialized successfully (read-only mode)")
        
    def _low_state_handler(self, msg: 'LowState_'):
        """Internal callback for low state messages"""
        self.low_state = msg
        
        if self.use_motion_switcher and not self.update_mode_machine:
            self.mode_machine = self.low_state.mode_machine
            self.update_mode_machine = True
    
    def get_joint_state(self) -> Optional[JointState]:
        """
        Get current joint state.
        
        Returns:
            JointState object or None if not available
        """
        if self.low_state is None:
            return None
            
        positions = np.array([self.low_state.motor_state[i].q for i in range(self.num_motors)])
        velocities = np.array([self.low_state.motor_state[i].dq for i in range(self.num_motors)])
        torques = np.array([self.low_state.motor_state[i].tau_est for i in range(self.num_motors)])
        
        return JointState(
            positions=positions,
            velocities=velocities,
            torques=torques,
            timestamp=time.time()
        )
    
    def set_passive_mode(self, joint_indices: Optional[list] = None, continuous: bool = False):
        """
        Set motors to passive mode (zero torque, free movement).
        Useful for recording.
        
        Note: This command should be sent continuously (e.g., at 50Hz) during recording
        to minimize residual resistance. Single calls may leave some motor damping active.
        
        Args:
            joint_indices: List of joint indices to set passive. If None, sets all motors.
            continuous: If True, suppress status messages (for continuous calling)
        """
        if not self.is_initialized:
            raise RuntimeError("Interface not initialized. Call initialize() first.")
        
        if not self.use_motion_switcher:
            raise RuntimeError("Motion switcher not enabled. Initialize with use_motion_switcher=True")
        
        if joint_indices is None:
            joint_indices = list(range(self.num_motors))
            if not continuous:
                print("Setting all motors to passive mode...")
        else:
            if not continuous:
                print(f"Setting {len(joint_indices)} motors to passive mode...")
            
        # Set specified motors to disabled with zero gains
        # mode=0: Disable motor control
        # kp=0, kd=0: Zero position and velocity gains
        # tau=0: Zero feedforward torque
        self.low_cmd.mode_pr = Mode.PR
        self.low_cmd.mode_machine = self.mode_machine
        
        for i in joint_indices:
            self.low_cmd.motor_cmd[i].mode = 0  # Disable motor
            self.low_cmd.motor_cmd[i].q = 0.0
            self.low_cmd.motor_cmd[i].dq = 0.0
            self.low_cmd.motor_cmd[i].tau = 0.0
            self.low_cmd.motor_cmd[i].kp = 0.0
            self.low_cmd.motor_cmd[i].kd = 0.0
        
        # Send command
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_publisher.Write(self.low_cmd)
    
    def send_joint_commands(self, 
                           positions: np.ndarray,
                           velocities: Optional[np.ndarray] = None,
                           torques: Optional[np.ndarray] = None,
                           kp: Optional[np.ndarray] = None,
                           kd: Optional[np.ndarray] = None,
                           joint_indices: Optional[list] = None):
        """
        Send joint position commands to robot.
        
        Args:
            positions: Target joint positions (29,) in radians
            velocities: Target joint velocities (29,) in rad/s (optional)
            torques: Feedforward torques (29,) in Nm (optional)
            kp: Position gains (29,) (optional, uses defaults if None)
            kd: Velocity gains (29,) (optional, uses defaults if None)
            joint_indices: List of joint indices to command. If None, commands all joints.
        """
        if not self.is_initialized:
            raise RuntimeError("Interface not initialized. Call initialize() first.")
        
        if not self.use_motion_switcher:
            raise RuntimeError("Motion switcher not enabled. Initialize with use_motion_switcher=True")
        
        if len(positions) != self.num_motors:
            raise ValueError(f"Expected {self.num_motors} positions, got {len(positions)}")
        
        # Use defaults if not provided
        if kp is None:
            kp = np.array(DEFAULT_KP)
        if kd is None:
            kd = np.array(DEFAULT_KD)
        if velocities is None:
            velocities = np.zeros(self.num_motors)
        if torques is None:
            torques = np.zeros(self.num_motors)
        
        # Determine which joints to command
        if joint_indices is None:
            joint_indices = list(range(self.num_motors))
        
        # Set command
        self.low_cmd.mode_pr = Mode.PR
        self.low_cmd.mode_machine = self.mode_machine
        
        for i in joint_indices:
            self.low_cmd.motor_cmd[i].mode = 1  # Enable
            self.low_cmd.motor_cmd[i].q = float(positions[i])
            self.low_cmd.motor_cmd[i].dq = float(velocities[i])
            self.low_cmd.motor_cmd[i].tau = float(torques[i])
            self.low_cmd.motor_cmd[i].kp = float(kp[i])
            self.low_cmd.motor_cmd[i].kd = float(kd[i])
        
        # Send command
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_publisher.Write(self.low_cmd)
    
    def start_control_loop(self, control_function, frequency: float = 500.0):
        """
        Start a control loop at specified frequency.
        
        Args:
            control_function: Function to call each iteration (takes no args)
            frequency: Control loop frequency in Hz
        """
        if self.is_control_active:
            raise RuntimeError("Control loop already active")
        
        interval = 1.0 / frequency
        self.control_thread = RecurrentThread(
            interval=interval,
            target=control_function,
            name="g1_control"
        )
        self.control_thread.Start()
        self.is_control_active = True
        print(f"Control loop started at {frequency} Hz")
    
    def stop_control_loop(self):
        """Stop the control loop"""
        if self.control_thread:
            self.control_thread.Stop()
            self.is_control_active = False
            print("Control loop stopped")
    
    def shutdown(self):
        """Cleanup and shutdown"""
        print("Shutting down G1 interface...")
        
        if self.is_control_active:
            self.stop_control_loop()
        
        # Set passive mode before shutdown (only if we have control)
        if self.is_initialized and self.use_motion_switcher:
            try:
                self.set_passive_mode()
                time.sleep(0.1)
            except Exception as e:
                print(f"Warning: Failed to set passive mode during shutdown: {e}")
        
        self.is_initialized = False
        print("G1 interface shutdown complete")

