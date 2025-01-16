# examples/verify_connection.py

from disting_nt.communication.midi_interface import MidiInterface
from disting_nt.communication.sysex_handler import SysExHandler
import time
import logging
import warnings
import rtmidi

def main():
    # Suppress rtmidi warning about the GIL
    warnings.filterwarnings("ignore", category=UserWarning, module="rtmidi")
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize MIDI interface
    midi = MidiInterface()
    if not midi.connect():
        logger.error("Failed to connect to Disting NT")
        return
        
    # Initialize SysEx handler
    sysex = SysExHandler(midi)
    
    # Test communication by requesting preset name
    preset_name = sysex.request_preset_name()
    if preset_name:
        logger.info(f"Current preset: {preset_name}")
    else:
        logger.error("Failed to get preset name")
        
    # Clean up
    midi.close()

if __name__ == "__main__":
    main()