# communication/sysex_handler.py

from typing import List, Optional
from .midi_interface import MidiInterface
from ..messages.commands import SysExCommands, SysExHeaders
import time
import logging

class SysExHandler:
    def __init__(self, midi_interface: MidiInterface):
        self.midi = midi_interface
        self.last_response = None
        self.logger = logging.getLogger(__name__)
        
    def _verify_header(self, data: List[int]) -> bool:
        """Verify SysEx message header matches Disting NT"""
        if len(data) < 6:
            return False
            
        expected_header = [
            SysExHeaders.MANUFACTURER_ID[0],
            SysExHeaders.MANUFACTURER_ID[1],
            SysExHeaders.MANUFACTURER_ID[2],
            SysExHeaders.DEVICE_ID,
            self.midi.sysex_id
        ]
        
        # Debug logging to see what we're comparing
        self.logger.debug(f"Expected header: {[hex(b) for b in expected_header]}")
        self.logger.debug(f"Received header: {[hex(b) for b in data[:5]]}")
        
        # Compare each byte
        for i, (expected, received) in enumerate(zip(expected_header, data[:5])):
            if expected != received:
                self.logger.debug(f"Header mismatch at position {i}: expected {hex(expected)}, got {hex(received)}")
                return False
                
        return True
        
    def request_preset_name(self) -> Optional[str]:
        """Request and decode the current preset name"""
        self.last_response = None
        
        def preset_name_callback(msg):
            if not self._verify_header(msg.data):
                self.logger.warning("Received message with invalid header")
                return
                
            if msg.data[5] == SysExCommands.GET_PRESET_NAME:
                # Extract name from sysex data
                name_data = msg.data[6:-1]  # Skip header and end marker
                self.last_response = ''.join(chr(b) for b in name_data if b != 0)
                self.logger.info(f"Received preset name: {self.last_response}")
                
        self.midi.set_callback(preset_name_callback)
        if not self.midi.send_sysex(SysExCommands.GET_PRESET_NAME):
            return None
        
        # Wait for response
        timeout = time.time() + 1.0  # 1 second timeout
        while time.time() < timeout and self.last_response is None:
            time.sleep(0.01)
            
        if self.last_response is None:
            self.logger.warning("Timeout waiting for preset name response")
            
        return self.last_response

    def request_algorithm_count(self):
        """Request the total number of available algorithms"""
        self.last_response = None
        
        def algorithm_count_callback(msg):
            if not self._verify_header(msg.data):
                self.logger.warning("Received message with invalid header")
                return
                
            if msg.data[5] == 0x30:  # Algorithm count command
                # The count is in the last byte (0x42 = 66 algorithms)
                count = msg.data[-1]  # Get last byte before end marker
                self.last_response = count
                self.logger.debug(f"Received algorithm count: {count}")
        
        self.midi.set_callback(algorithm_count_callback)
        if not self.midi.send_sysex_command(0x30):  # Use send_sysex_command for simple commands
            return None
        
        # Wait for response
        timeout = time.time() + 1.0  # 1 second timeout
        while time.time() < timeout and self.last_response is None:
            time.sleep(0.01)
            
        if self.last_response is None:
            self.logger.warning("Timeout waiting for algorithm count response")
            
        return self.last_response

    def request_algorithm_info(self, index):
        """Request information about a specific algorithm
        
        SysEx Message Format:
        --------------------
        Header (6 bytes):
            [0x0, 0x21, 0x27, 0x6d, 0x0, 0x31]
            - Manufacturer ID (3 bytes)
            - Device ID (1 byte)
            - SysEx ID (1 byte)
            - Command byte (0x31 for algorithm info)
        
        Data Format:
        -----------
        1. Algorithm ID (4 bytes)
        2. Short name (null-terminated string)
        3. Control sequence (11 bytes):
           [0x1, 0x0, 0x0, 0x1, 0x0, 0x0, 0x8, 0x0, 0x0, 0x1, 0x0]
        4. Full name (null-terminated string)
        5. Additional data (specs, etc.)
        
        Example:
        --------
        0x0 0x21 0x27 0x6d 0x0 0x31   # Header
        [4 bytes ID]                    # Algorithm ID
        0x76 0x63 0x61 0x6d 0x0        # Short name "vcam"
        0x1 0x0 0x0 0x1 0x0 0x0 0x8 0x0 0x0 0x1 0x0  # Control sequence
        0x56 0x43 0x41 ... 0x0         # Full name "VCA/Multiplier"
        """
        self.last_response = None
        
        def algorithm_info_callback(msg):
            if not self._verify_header(msg.data):
                self.logger.warning("Received message with invalid header")
                return
                
            if msg.data[5] == 0x31:  # Algorithm info command
                # Log raw data for detailed debugging
                self.logger.debug(f"Algorithm {index} raw data:")
                self.logger.debug(f"  Hex:   {' '.join(hex(b) for b in msg.data)}")
                
                # Format ASCII with dots for non-printable chars
                ascii_chars = []
                for b in msg.data:
                    if 32 <= b <= 126:  # Printable ASCII range
                        ascii_chars.append(chr(b))
                    else:
                        ascii_chars.append('·')  # Use middle dot for non-printable
                self.logger.debug(f"  ASCII: {''.join(ascii_chars)}")
                
                # Extract data after header and command byte
                data = msg.data[6:-1]  # Skip header (5) + command (1) and end marker
                if len(data) < 4:
                    self.logger.warning(f"Algorithm {index} response too short: {len(data)} bytes")
                    return
                    
                try:
                    # Parse algorithm info from response
                    result = {}
                    
                    # Step 1: Extract short name (after 4-byte ID, until first null)
                    short_name_end = data.index(0, 4)  # Start looking after ID
                    result['short_name'] = ''.join(chr(b) for b in data[4:short_name_end])
                    
                    # Step 2: Look for the control sequence that precedes the full name
                    # This sequence appears to be consistent across all algorithm messages
                    control_sequence = [0x1, 0x0, 0x0, 0x1, 0x0, 0x0, 0x8, 0x0, 0x0, 0x1, 0x0]
                    
                    # Step 3: Find where the control sequence starts
                    for i in range(short_name_end, len(data) - len(control_sequence)):
                        if data[i:i+len(control_sequence)] == control_sequence:
                            # Full name starts immediately after control sequence
                            name_start = i + len(control_sequence)
                            try:
                                name_end = data.index(0, name_start)  # Find null terminator
                                result['name'] = ''.join(chr(b) for b in data[name_start:name_end])
                            except ValueError:
                                # If no null terminator, use rest of data
                                result['name'] = ''.join(chr(b) for b in data[name_start:])
                            break
                    else:
                        # Fallback: If control sequence not found, try looking for uppercase letters
                        # (Full names always start with uppercase)
                        for i in range(short_name_end, len(data)):
                            if 65 <= data[i] <= 90:  # ASCII uppercase A-Z
                                try:
                                    name_end = data.index(0, i)
                                    result['name'] = ''.join(chr(b) for b in data[i:name_end])
                                    break
                                except ValueError:
                                    result['name'] = ''.join(chr(b) for b in data[i:])
                                    break
                    
                    if 'name' not in result:
                        self.logger.warning(f"Could not find full name for algorithm {index}")
                        result['name'] = result['short_name'].upper()
                    
                    self.logger.debug(f"  Parsed: short_name='{result['short_name']}' full_name='{result['name']}'")
                    self.last_response = result
                    
                except Exception as e:
                    self.logger.error(f"Error parsing algorithm {index} info: {str(e)}")
                    self.logger.debug(f"  Raw data: {' '.join(f'[{hex(b)}]' for b in data)}")
        
        self.midi.set_callback(algorithm_info_callback)
        
        # Send algorithm info request
        msg = [
            0x31,  # Algorithm info command
            (index >> 14) & 0x03,  # High bits
            (index >> 7) & 0x7F,   # Middle bits
            index & 0x7F           # Low bits
        ]
        self.logger.debug(f"Requesting algorithm {index} info: {' '.join(hex(b) for b in msg)}")
        
        if not self.midi.send_sysex(msg):
            return None
        
        # Wait for response
        timeout = time.time() + 1.0  # 1 second timeout
        while time.time() < timeout and self.last_response is None:
            time.sleep(0.01)
            
        if self.last_response is None:
            self.logger.warning(f"Timeout waiting for algorithm {index+1} info response")
            
        return self.last_response