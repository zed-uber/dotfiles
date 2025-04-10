#!/usr/bin/env python3

import subprocess
import json
import re
from typing import List, Dict, Optional

def run_pactl_command(command: str) -> str:
    """Run a pactl command and return its output."""
    try:
        result = subprocess.run(['pactl'] + command.split(), 
                              capture_output=True, 
                              text=True, 
                              check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return ""

def get_sinks() -> List[Dict]:
    """Get all audio output devices (sinks)."""
    output = run_pactl_command("list sinks short")
    sinks = []
    
    for line in output.splitlines():
        if not line.strip():
            continue
            
        parts = line.split()
        if len(parts) >= 2:
            sink = {
                'index': parts[0],
                'name': parts[1],
                'state': parts[2] if len(parts) > 2 else 'unknown'
            }
            sinks.append(sink)
    
    return sinks

def get_sink_info(sink_index: str) -> Dict:
    """Get detailed information about a specific sink."""
    output = run_pactl_command("list sinks")
    sinks = {}
    current_sink = None
    
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Sink #'):
            current_sink = line.split('#')[1].strip()
            sinks[current_sink] = {}
        elif current_sink and ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            sinks[current_sink][key] = value.strip()
            
    return sinks.get(sink_index, {})

def get_playback_streams() -> List[Dict]:
    """Get all active playback streams."""
    output = run_pactl_command("list sink-inputs short")
    streams = []
    
    for line in output.splitlines():
        if not line.strip():
            continue
            
        parts = line.split()
        if len(parts) >= 2:
            stream = {
                'index': parts[0],
                'sink': parts[1],
                'state': parts[2] if len(parts) > 2 else 'unknown'
            }
            streams.append(stream)
    
    return streams

def move_stream_to_sink(stream_index: str, sink_index: str) -> bool:
    """Move a playback stream to a different sink."""
    try:
        run_pactl_command(f"move-sink-input {stream_index} {sink_index}")
        return True
    except subprocess.CalledProcessError:
        return False

def get_next_sink_index(current_sink_index: Optional[str] = None) -> str:
    """Get the next sink index in a circular manner."""
    sinks = get_sinks()
    if not sinks:
        return "0"
        
    if current_sink_index is None:
        return sinks[0]['index']
        
    # Find current sink index in the list
    current_idx = -1
    for i, sink in enumerate(sinks):
        if sink['index'] == current_sink_index:
            current_idx = i
            break
            
    if current_idx == -1:
        return sinks[0]['index']
        
    # Get next sink index (circular)
    next_idx = (current_idx + 1) % len(sinks)
    return sinks[next_idx]['index']

def cycle_all_streams_to_next_sink() -> bool:
    """Move all streams to the next available sink."""
    streams = get_playback_streams()
    if not streams:
        return False
        
    # Get the sink of the first stream as reference
    current_sink = streams[0]['sink']
    next_sink = get_next_sink_index(current_sink)
    
    # Move all streams to the next sink
    success = True
    for stream in streams:
        if not move_stream_to_sink(stream['index'], next_sink):
            success = False
            
    return success

def clean_sink_name(sink_name: str) -> str:
    """Clean and shorten sink names to more concise labels."""
    # Convert to lowercase for easier matching
    name_lower = sink_name.lower()
    
    # Handle SteelSeries Arctis specifically
    if 'arctis' in name_lower:
        if 'stereo-game' in name_lower or 'game' in name_lower:
            return "Game"
        elif 'mono-chat' in name_lower or 'chat' in name_lower:
            return "Chat"
        return "Arctis"
    
    # Handle PCI/analog output
    if ('pci' in name_lower and 'analog' in name_lower) or 'analog-stereo' in name_lower:
        return "Stereo"
    
    # If no specific match, return a cleaned version of the name
    name = sink_name.split('.')[-1].replace('analog-stereo', '').replace('_', ' ').replace('-', ' ')
    return name.strip().title()

def get_current_sink_status() -> Dict:
    """Get current sink status in a format compatible with waybar pulseaudio module."""
    streams = get_playback_streams()
    if not streams:
        return {
            "volume": 0,
            "icon": "󰋎",  # headphone icon
            "muted": True,
            "sink_name": "No active streams"
        }
    
    # Get the sink that most streams are using
    sink_counts = {}
    for stream in streams:
        sink = stream['sink']
        sink_counts[sink] = sink_counts.get(sink, 0) + 1
    
    most_used_sink = max(sink_counts.items(), key=lambda x: x[1])[0]
    
    # Get all sinks
    sinks = get_sinks()
    sink_name = "Unknown"
    for sink in sinks:
        if sink['index'] == most_used_sink:
            sink_name = sink['name']
            break
    
    # Clean up the sink name
    clean_name = clean_sink_name(sink_name)
    
    # Get sink info for volume and mute status
    sink_info = get_sink_info(most_used_sink)
    
    # Parse volume from sink info (default to 100% if not found)
    volume_str = sink_info.get('volume', '100%')
    if isinstance(volume_str, str):
        volume_match = re.search(r'(\d+)%', volume_str)
        volume = int(volume_match.group(1)) if volume_match else 100
    else:
        volume = 100
    
    # Determine if muted
    muted = sink_info.get('mute', 'no').lower() == 'yes'
    
    return {
        "volume": volume,
        "icon": "󰕾" if volume > 50 else "󰕿",  # speaker icons
        "muted": muted,
        "sink_name": clean_name
    }

if __name__ == "__main__":
    status = get_current_sink_status()
    print(json.dumps({
        "text": f"{status['icon']} {status['sink_name']}",
        "tooltip": "Click to cycle audio outputs"
    }))