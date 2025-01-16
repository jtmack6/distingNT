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
        
    def wake(self):
        """Send wake command to ensure device is ready
        
        SysEx Message Format:
        --------------------
        Command byte: 0x07 (WAKE)
        No additional data
        
        Example from WebUI:
        F0 00 21 27 6D 00 07 F7
        """
        self.logger.debug("Sending wake command")
        # Send wake command and wait for response
        if not self.midi.send_sysex_command(SysExCommands.WAKE):
            return False
        
        # Wait for device to respond
        time.sleep(0.1)
        return True

    def initialize(self):
        """Initialize communication with Disting NT
        
        Follows the WebUI sequence:
        1. Request algorithm names
        2. Request preset name
        3. Request unit strings
        4. Request num parameters
        5. Request num algorithms
        6. Send RTC update
        7. Request parameter values
        """
        self.logger.debug("Initializing communication with Disting NT")
        
        # Send wake command first
        if not self.wake():
            self.logger.error("Failed to wake device")
            return False
        
        # Request algorithm names
        if not self.midi.send_sysex_command(SysExCommands.GET_ALGORITHM_NAMES):
            return False
        
        # Request preset name
        if not self.midi.send_sysex([SysExCommands.GET_PRESET_NAME, 0x50]):
            return False
        
        # Request unit strings
        if not self.midi.send_sysex_command(SysExCommands.GET_UNIT_STRINGS):
            return False
        
        # Request num parameters
        if not self.midi.send_sysex_command(SysExCommands.GET_NUM_PARAMETERS):
            return False
        
        # Request num algorithms
        if not self.midi.send_sysex_command(SysExCommands.GET_ALGORITHM_COUNT):
            return False
        
        # Send RTC update
        current_time = time.localtime()
        rtc_data = [
            SysExCommands.SET_RTC,
            current_time.tm_hour,
            current_time.tm_min,
            current_time.tm_sec
        ]
        if not self.midi.send_sysex(rtc_data):
            return False
        
        # Request parameter values
        if not self.midi.send_sysex_command(SysExCommands.GET_PARAMETER_VALUES):
            return False
        
        self.logger.debug("Initialization sequence completed")
        return True

    def request_preset_name(self):
        """Request the current preset name from the Disting NT
        
        SysEx Message Format:
        --------------------
        Request:
            F0 00 21 27 6D 00 41 F7
        
        Response:
            Header: F0 00 21 27 6D 00
            Command: 41
            Data: Up to 21 bytes of ASCII text, null terminated
            Example: F0 00 21 27 6D 00 41 41 6C 65 61 ... 00
                                         ^cmd ^A ^l ^e ^a
        """
        self.last_response = None
        
        def preset_name_callback(msg):
            if not self._verify_header(msg.data):
                self.logger.warning("Received message with invalid header")
                return
                
            if msg.data[5] == SysExCommands.GET_PRESET_NAME:
                # Get raw name data (up to 21 bytes) starting after command byte
                name_data = msg.data[6:]  # Skip header (5) + command (1)
                
                try:
                    # Process up to 21 chars until null terminator
                    name = ""
                    for i in range(min(21, len(name_data))):
                        if name_data[i] == 0:
                            break
                        name += chr(name_data[i])
                    
                    self.logger.debug(f"Raw preset name bytes: {[hex(b) for b in name_data]}")
                    self.logger.debug(f"Parsed preset name: '{name}'")
                    self.last_response = name
                except Exception as e:
                    self.logger.error(f"Error parsing preset name: {str(e)}")
                    self.logger.debug(f"Raw name data: {[hex(b) for b in name_data]}")
        
        self.midi.set_callback(preset_name_callback)
        
        # Send wake command first
        if not self.wake():
            self.logger.error("Failed to wake device")
            return None
        
        # Send preset name request - command 0x41 with no data
        msg = [SysExCommands.GET_PRESET_NAME]  # Just the command byte
        self.logger.debug(f"Requesting preset name with command: {hex(SysExCommands.GET_PRESET_NAME)}")
        
        if not self.midi.send_sysex_command(SysExCommands.GET_PRESET_NAME):
            return None
        
        # Wait for response
        timeout = time.time() + 2.0
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