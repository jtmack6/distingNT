# communication/midi_interface.py

import mido
from typing import Optional, List, Callable
import time
import logging
from ..messages.commands import SysExHeaders

class MidiInterface:
    def __init__(self, port_name: str = "disting NT", sysex_id: int = 0):
        self.port_name = port_name
        self.sysex_id = sysex_id
        self.input_port: Optional[mido.ports.BaseInput] = None
        self.output_port: Optional[mido.ports.BaseOutput] = None
        self.callback: Optional[Callable] = None
        self.logger = logging.getLogger(__name__)
        
    def set_callback(self, callback: Callable):
        """Set callback for incoming messages"""
        self.callback = callback
        
    def connect(self) -> bool:
        """Establish connection to the Disting NT"""
        try:
            available_inputs = mido.get_input_names()
            available_outputs = mido.get_output_names()
            
            self.logger.info(f"Available MIDI inputs: {available_inputs}")
            self.logger.info(f"Available MIDI outputs: {available_outputs}")
            
            if self.port_name not in available_inputs or self.port_name not in available_outputs:
                self.logger.error(f"Disting NT ports not found")
                raise ValueError(f"Disting NT ports not found. Available ports: {available_inputs}")
            
            self.input_port = mido.open_input(self.port_name, callback=self._message_callback)
            self.output_port = mido.open_output(self.port_name)
            
            self.logger.info(f"Successfully connected to Disting NT")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
            
    def _message_callback(self, msg):
        """Handle incoming MIDI messages"""
        if msg.type == 'sysex':
            self.logger.debug(f"Received SysEx: {[hex(b) for b in msg.data]}")
            if self.callback:
                self.callback(msg)
    
    def _validate_sysex_data(self, data: List[int]) -> List[int]:
        """Ensure all data bytes are in valid MIDI range (0-127)"""
        return [b & 0x7F for b in data]  # Mask to 7 bits
            
    def send_sysex(self, msg):
        """Send a SysEx message to the device"""
        try:
            # Add SysEx header and end marker
            full_msg = [
                SysExHeaders.MANUFACTURER_ID[0],
                SysExHeaders.MANUFACTURER_ID[1], 
                SysExHeaders.MANUFACTURER_ID[2],
                SysExHeaders.DEVICE_ID,
                self.sysex_id
            ]
            
            # If msg is a single integer, convert to list
            if isinstance(msg, int):
                full_msg.append(msg)
            else:
                full_msg.extend(msg)
                
            # Log the message we're sending
            self.logger.debug(f"Sending SysEx: {[hex(b) for b in full_msg]}")
            
            # Create and send mido message
            message = mido.Message('sysex', data=full_msg)
            self.output_port.send(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending SysEx: {str(e)}")
            return False
            
    def send_sysex_command(self, command: int, data: List[int] = None) -> bool:
        """Send a SysEx command with optional data to the Disting NT"""
        try:
            if not self.output_port:
                raise RuntimeError("Not connected to Disting NT")
            
            # Build message data
            msg_data = [
                SysExHeaders.MANUFACTURER_ID[0] & 0x7F,
                SysExHeaders.MANUFACTURER_ID[1] & 0x7F,
                SysExHeaders.MANUFACTURER_ID[2] & 0x7F,
                SysExHeaders.DEVICE_ID & 0x7F,
                self.sysex_id & 0x7F,
                command & 0x7F
            ]
            
            # Add optional data bytes
            if data:
                msg_data.extend([b & 0x7F for b in data])
            
            # Create and send message
            message = mido.Message('sysex', data=msg_data)
            self.logger.debug(f"Sending SysEx command: {[hex(b) for b in message.data]}")
            self.output_port.send(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending SysEx command: {str(e)}")
            return False
            
    def close(self):
        """Close MIDI connections"""
        if self.input_port:
            self.input_port.close()
        if self.output_port:
            self.output_port.close()