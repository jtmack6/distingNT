import warnings
import rtmidi
import argparse
# Suppress all RuntimeWarnings from importlib about the GIL
warnings.filterwarnings("ignore", category=RuntimeWarning, module="importlib._bootstrap")

from disting_nt.communication.midi_interface import MidiInterface
from disting_nt.communication.sysex_handler import SysExHandler
import logging

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='List available algorithms on the Disting NT')
    parser.add_argument('--show-short-names', action='store_true',
                      help='Show short names alongside full names')
    parser.add_argument('-v', '--verbose', choices=['info', 'debug'],
                      help='Set verbosity level (info or debug)')
    args = parser.parse_args()

    # Setup logging
    if args.verbose == 'debug':
        log_level = logging.DEBUG
    elif args.verbose == 'info':
        log_level = logging.INFO
    else:
        # Only show warnings and errors by default
        log_level = logging.WARNING
        
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set log level for all loggers in our package
    logging.getLogger('disting_nt').setLevel(log_level)
    logger = logging.getLogger(__name__)
    
    # Initialize MIDI interface
    midi = MidiInterface()
    if not midi.connect():
        logger.error("Failed to connect to Disting NT")
        return
        
    # Initialize SysEx handler
    sysex = SysExHandler(midi)
    
    # Get algorithm count
    count = sysex.request_algorithm_count()
    if count is None:
        logger.error("Failed to get algorithm count")
        return
        
    print(f"Found {count} algorithms:")
    print("-" * 40)
    
    # Request info for each algorithm
    for i in range(count):
        algo_info = sysex.request_algorithm_info(i)
        if algo_info and 'name' in algo_info:
            if args.show_short_names:
                # Show both full name and short name
                print(f"{i+1:2d}. {algo_info['name']:<35} [{algo_info['short_name']}]")
            else:
                # Show only full name
                print(f"{i+1:2d}. {algo_info['name']:<35}")
        else:
            logger.warning(f"Failed to get info for algorithm {i+1}")
    
    print("-" * 40)
    
    # Clean up
    midi.close()

if __name__ == "__main__":
    main() 