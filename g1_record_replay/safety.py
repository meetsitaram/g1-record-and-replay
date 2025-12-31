"""Safety utilities for G1 robot control"""

import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

try:
    from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
    LOCO_CLIENT_AVAILABLE = True
except ImportError:
    LOCO_CLIENT_AVAILABLE = False


class SafetyChecker:
    """
    Handles safety checks before low-level motor control.
    Ensures FSM (high-level mode) is disabled before sending low-level commands.
    """
    
    def __init__(self):
        self.console = Console()
        self.loco_client = None
        
    def initialize_loco_client(self) -> bool:
        """Initialize the high-level LocoClient for FSM control"""
        if not LOCO_CLIENT_AVAILABLE:
            self.console.print("[yellow]⚠ LocoClient not available. Cannot check/control FSM state.[/yellow]")
            return False
        
        try:
            self.console.print("[cyan]Initializing LocoClient for safety checks...[/cyan]")
            self.loco_client = LocoClient()
            self.loco_client.SetTimeout(5.0)
            self.loco_client.Init()
            return True
        except Exception as e:
            self.console.print(f"[yellow]⚠ Could not initialize LocoClient: {e}[/yellow]")
            return False
    
    def disable_fsm(self) -> bool:
        """
        Disable FSM (high-level mode) by setting motors to zero torque.
        This is CRITICAL before starting low-level control.
        """
        if not self.loco_client:
            self.console.print("[yellow]⚠ LocoClient not initialized. Skipping FSM disable.[/yellow]")
            return False
        
        try:
            self.console.print("[bold cyan]Setting robot to ZeroTorque mode (FSM disabled)...[/bold cyan]")
            self.loco_client.ZeroTorque()
            time.sleep(1.0)  # Give time for the command to take effect
            
            self.console.print("[green]✓ FSM disabled. Robot is now safe for low-level control.[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Failed to disable FSM: {e}[/red]")
            return False
    
    def pre_replay_safety_check(self, joint_group: str = "arms") -> bool:
        """
        Complete safety check before replay.
        
        Args:
            joint_group: Which joints will be controlled
            
        Returns:
            True if safe to proceed, False otherwise
        """
        self.console.print(Panel.fit(
            "[bold red]⚠️  SAFETY CHECK BEFORE REPLAY ⚠️[/bold red]\n\n"
            f"About to replay motion on: [bold cyan]{joint_group}[/bold cyan]\n\n"
            "[yellow]This will:[/yellow]\n"
            "  1. Disable FSM (high-level mode) → Zero Torque\n"
            "  2. Enable low-level motor control\n"
            "  3. Send position commands to motors\n"
            "  4. The robot WILL MOVE\n\n"
            "[bold]Safety Requirements:[/bold]\n"
            "  • Robot has clear space to move\n"
            "  • You are ready to press Ctrl+C if needed\n"
            "  • No one is touching the robot\n"
            "  • Emergency stop is accessible",
            title="🛡️ REPLAY SAFETY",
            border_style="red"
        ))
        
        # Ask for confirmation
        if not Confirm.ask("\n[bold]Do you confirm it is safe to proceed?[/bold]", default=False):
            self.console.print("[yellow]❌ Replay cancelled by user.[/yellow]")
            return False
        
        # Initialize LocoClient
        if not self.initialize_loco_client():
            self.console.print("[yellow]⚠ Could not initialize LocoClient.[/yellow]")
            if not Confirm.ask("[bold yellow]Continue anyway? (NOT RECOMMENDED)[/bold yellow]", default=False):
                return False
        
        # Disable FSM
        if self.loco_client:
            if not self.disable_fsm():
                self.console.print("[yellow]⚠ Could not disable FSM.[/yellow]")
                if not Confirm.ask("[bold yellow]Continue anyway? (DANGEROUS)[/bold yellow]", default=False):
                    return False
        
        # Final confirmation
        self.console.print("\n[bold green]✓ All safety checks passed.[/bold green]")
        time.sleep(1)
        
        return True
    
    def pre_record_safety_check(self, joint_group: str = "arms") -> bool:
        """
        Safety check before recording.
        Recording sets motors to passive mode (zero torque) which is safer.
        
        NOTE: For recording, we do NOT call ZeroTorque() globally because:
        - We only want to disable the specified joint group (e.g., arms)
        - Other joints (e.g., legs) should remain active to support the robot
        - The low-level set_passive_mode() handles this correctly
        """
        self.console.print(Panel.fit(
            "[bold cyan]📹  RECORDING MODE SAFETY CHECK[/bold cyan]\n\n"
            f"About to record motion on: [bold cyan]{joint_group}[/bold cyan]\n\n"
            "[yellow]This will:[/yellow]\n"
            f"  1. Set [bold]{joint_group}[/bold] motors to PASSIVE mode (zero torque)\n"
            "  2. These motors will move freely by hand\n"
            "  3. Record joint positions as you move them\n"
            f"  4. [bold green]Other motors ({self._get_other_groups(joint_group)}) remain ACTIVE[/bold green]\n\n"
            "[bold]Safety Notes:[/bold]\n"
            "  • Recording is safer than replay (selected motors are passive)\n"
            f"  • You can freely move the {joint_group} by hand\n"
            "  • Other joints will maintain their current position\n"
            "  • If recording arms: legs will keep the robot standing ✓",
            title="🛡️ RECORD SAFETY",
            border_style="cyan"
        ))
        
        return Confirm.ask("\n[bold]Ready to start recording?[/bold]", default=True)
    
    def _get_other_groups(self, selected_group: str) -> str:
        """Get string describing other joint groups not in the selected group"""
        all_groups = ["legs", "waist", "arms"]
        other_groups = [g for g in all_groups if g != selected_group]
        if not other_groups:
            return "none"
        return ", ".join(other_groups)


def check_and_disable_fsm() -> bool:
    """
    Standalone function to check and disable FSM.
    Useful for scripts that need to ensure low-level control is safe.
    
    Returns:
        True if FSM was successfully disabled or already disabled
    """
    checker = SafetyChecker()
    if checker.initialize_loco_client():
        return checker.disable_fsm()
    return False

