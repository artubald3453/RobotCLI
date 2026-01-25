import re
import time
from config import ALIASES, GROUPS, GPIO_PINS
import pinrun


def parse_command(command_string):
    """
    Parse a command in the format: alias_name(duration)
    Returns: (alias_name, duration_in_seconds) or (None, None) if invalid
    """
    match = re.match(r'(\w+)\(([0-9.]+)\)', command_string.strip())
    if not match:
        return None, None
    
    alias_name = match.group(1)
    try:
        duration = float(match.group(2))
    except ValueError:
        return None, None
    
    return alias_name, duration


def execute_command(alias_name, duration):
    """
    Execute a command by:
    1. Resolving alias to config_spotX
    2. Resolving config_spotX to pin number
    3. Calling pin{N}_on() for duration seconds
    4. Calling pin{N}_off()
    """
    # Check if alias exists
    if alias_name not in ALIASES:
        print(f"Error: Unknown alias '{alias_name}'")
        return False
    
    # Get the config_spotX name
    config_spot = ALIASES[alias_name]
    
    # Get the pin number
    if config_spot not in GPIO_PINS:
        print(f"Error: Unknown config spot '{config_spot}'")
        return False
    
    pin_number = GPIO_PINS[config_spot]
    
    try:
        # Get the on/off functions for this pin
        pin_on_func = getattr(pinrun, f'pin{pin_number}_on')
        pin_off_func = getattr(pinrun, f'pin{pin_number}_off')
        
        # Activate the pin
        print(f"Activating {alias_name} (pin {pin_number}) for {duration} seconds...")
        pin_on_func()
        
        # Wait for the specified duration
        time.sleep(duration)
        
        # Deactivate the pin
        pin_off_func()
        print(f"Deactivated {alias_name} (pin {pin_number})")
        return True
    
    except AttributeError:
        print(f"Error: Pin {pin_number} functions not found in pinrun")
        return False
    except Exception as e:
        print(f"Error executing command: {e}")
        return False


def main():
    """Main loop to accept terminal commands"""
    print("RobotCLI Parser Started")
    print("Format: alias_name(duration_in_seconds)")
    print("Example: motor_1(2.5)")
    print("Type 'quit' to exit\n")
    
    try:
        while True:
            user_input = input(">>> ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("Exiting...")
                break
            
            if not user_input:
                continue
            
            alias_name, duration = parse_command(user_input)
            
            if alias_name is None:
                print("Invalid format. Use: alias_name(duration)")
                continue
            
            if duration <= 0:
                print("Error: Duration must be positive")
                continue
            
            execute_command(alias_name, duration)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        pinrun.cleanup()
        print("GPIO cleanup completed")


if __name__ == "__main__":
    main()