from typing import Optional, Dict, List
from .midi_handler import MIDIHandler

class DistingNTEditor:
    MANUFACTURER_ID = [0x00, 0x21, 0x27]
    DEVICE_ID = 0x6D
    
    def __init__(self):
        self.midi = MIDIHandler()
        self.sysex_id = 0
        self.current_slot = 0
        self.parameters: Dict = {}
        self.algorithms: List = []
        
    def connect(self, port_name: str = "disting NT") -> bool:
        """Connect to the Disting NT device."""
        success = self.midi.connect(port_name)
        if success:
            self.midi.set_callback(self._handle_sysex)
            self._send_wake()
        return success
        
    def _send_wake(self):
        """Send wake message to device."""
        self.send_sysex([0x07])
        
    def send_sysex(self, data: List[int]):
        """Send a SysEx message with proper headers."""
        message = (
            self.MANUFACTURER_ID +
            [self.DEVICE_ID, self.sysex_id] +
            data
        )
        self.midi.send_sysex(message)
        
    def _handle_sysex(self, data: List[int]):
        """Process incoming SysEx messages."""
        if not self._validate_sysex_header(data):
            return
            
        command = data[6]
        payload = data[7:-1]  # Remove header and end marker
        
        handlers = {
            0x30: self._handle_num_algorithms,
            0x31: self._handle_algorithm_info,
            0x40: self._handle_algorithm,
            0x41: self._handle_preset_name,
            # Add more handlers as needed
        }
        
        if command in handlers:
            handlers[command](payload)
            
    def _validate_sysex_header(self, data: List[int]) -> bool:
        """Validate incoming SysEx message header."""
        if len(data) < 7:
            return False
            
        expected_header = [0xF0] + self.MANUFACTURER_ID + [self.DEVICE_ID, self.sysex_id]
        return data[:6] == expected_header
        
    def _handle_num_algorithms(self, data: List[int]):
        """Process number of algorithms message."""
        num = self._extract_short(data)
        print(f"Number of algorithms: {num}")
        
    def _handle_algorithm_info(self, data: List[int]):
        """Process algorithm info message."""
        pass  # To be implemented
        
    def _handle_algorithm(self, data: List[int]):
        """Process algorithm data message."""
        pass  # To be implemented
        
    def _handle_preset_name(self, data: List[int]):
        """Process preset name message."""
        name = ""
        for i in range(min(21, len(data))):
            if data[i] == 0:
                break
            name += chr(data[i])
        print(f"Preset name: {name}")
        
    @staticmethod
    def _extract_short(data: List[int]) -> int:
        """Extract a short value from SysEx data."""
        return ((data[0] << 14) | (data[1] << 7) | data[2]) 
        
    def get_algorithm_info(self):
        """
        Get information about the current algorithm.
        
        Returns:
            dict: A dictionary containing algorithm information with keys:
                - name: Algorithm name
                - description: Algorithm description
                - parameters: List of parameter dictionaries with 'name' and 'description' keys
        """
        # First ensure we're connected and get the current algorithm
        if not self.is_connected:
            return None
        
        # You'll need to implement the actual MIDI communication here
        # This is just an example structure
        return {
            'name': 'Algorithm Name',
            'description': 'Algorithm Description',
            'parameters': [
                {'name': 'Parameter 1', 'description': 'Description of parameter 1'},
                {'name': 'Parameter 2', 'description': 'Description of parameter 2'},
                # Add more parameters as needed
            ]
        } 