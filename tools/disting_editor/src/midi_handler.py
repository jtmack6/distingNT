import rtmidi
from typing import Optional, List, Callable
import time

class MIDIHandler:
    def __init__(self):
        self.midi_in = rtmidi.MidiIn()
        self.midi_out = rtmidi.MidiOut()
        self.callback: Optional[Callable] = None
        
    def list_ports(self) -> tuple[List[str], List[str]]:
        """Returns available input and output port names."""
        return (self.midi_in.get_ports(), self.midi_out.get_ports())

    def connect(self, port_name: str = "disting NT") -> bool:
        """Connect to MIDI input and output ports."""
        in_ports = self.midi_in.get_ports()
        out_ports = self.midi_out.get_ports()
        
        in_port_idx = next((i for i, name in enumerate(in_ports) if port_name in name), None)
        out_port_idx = next((i for i, name in enumerate(out_ports) if port_name in name), None)
        
        if in_port_idx is None or out_port_idx is None:
            return False
            
        self.midi_in.open_port(in_port_idx)
        self.midi_out.open_port(out_port_idx)
        self.midi_in.ignore_types(sysex=False)
        return True
        
    def set_callback(self, callback: Callable):
        """Set callback for incoming MIDI messages."""
        self.callback = callback
        self.midi_in.set_callback(self._handle_message)
        
    def _handle_message(self, message, timestamp):
        """Internal message handler that calls user callback."""
        if self.callback:
            self.callback(message[0])
            
    def send_sysex(self, data: List[int]):
        """Send a SysEx message."""
        message = [0xF0] + data + [0xF7]
        self.midi_out.send_message(message)
        time.sleep(0.01)  # Small delay to prevent message flooding 