#!/usr/bin/env python3

import json
import sys
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Add the script directory to Python path so we can import pactl_tools
sys.path.append(script_dir)

from pactl_tools import get_current_sink_status, cycle_all_streams_to_next_sink

def main():
    # Check if script was called with an argument (Waybar sends event data)
    if len(sys.argv) > 1:
        # Handle click event by cycling to next sink
        cycle_all_streams_to_next_sink()
    
    # Get current status
    status = get_current_sink_status()
    
    # Format output for Waybar
    icon = "󰕾" if status['volume'] > 50 else "󰕿"
    if status['muted']:
        text = f"󰖁 {status['sink_name']}"  # muted icon
    else:
        text = f"{status['volume']}% {icon} {status['sink_name']}"
    
    output = {
        "text": text,
        "tooltip": "Click to cycle audio outputs",
        "class": "muted" if status['muted'] else ""
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main() 