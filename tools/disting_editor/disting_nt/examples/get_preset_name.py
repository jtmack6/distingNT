import logging
import argparse
from disting_nt.communication.midi_interface import MidiInterface
from disting_nt.communication.sysex_handler import SysExHandler

def main():
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Initialize MIDI interface
    midi = MidiInterface()
    if not midi.connect():
        logger.error("Failed to connect to Disting NT")
        return
        
    # Initialize SysEx handler
    sysex = SysExHandler(midi)
    
    # Send wake command first
    if not sysex.wake():
        logger.error("Failed to wake device")
        return
        
    # Get preset name
    logger.info("Requesting preset name...")
    preset_name = sysex.request_preset_name()
    if preset_name:
        print(f"\nCurrent Preset: '{preset_name}'")
    else:
        logger.error("Failed to get preset name")
    
    # Clean up
    midi.close()

if __name__ == "__main__":
    main() 