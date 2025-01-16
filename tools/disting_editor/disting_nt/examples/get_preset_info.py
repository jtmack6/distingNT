import logging
import argparse
from disting_nt.communication.midi_interface import MidiInterface
from disting_nt.communication.sysex_handler import SysExHandler

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Get preset information from Disting NT')
    parser.add_argument('-v', '--verbose', choices=['info', 'debug'],
                      help='Set verbosity level (info or debug)')
    args = parser.parse_args()

    # Setup logging
    if args.verbose == 'debug':
        log_level = logging.DEBUG
    elif args.verbose == 'info':
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
        
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger('disting_nt').setLevel(log_level)
    logger = logging.getLogger(__name__)
    
    # Initialize MIDI interface
    midi = MidiInterface()
    if not midi.connect():
        logger.error("Failed to connect to Disting NT")
        return
        
    # Initialize SysEx handler
    sysex = SysExHandler(midi)
    
    # Get preset name
    logger.info("Requesting preset name...")
    preset_name = sysex.request_preset_name()
    if preset_name:
        print(f"\nCurrent Preset: {preset_name}")
    else:
        logger.error("Failed to get preset name")
    
    # Clean up
    midi.close()

if __name__ == "__main__":
    main() 