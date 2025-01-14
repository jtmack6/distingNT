import argparse
from .editor import DistingNTEditor

def main():
    parser = argparse.ArgumentParser(description='Disting NT Command Line Editor')
    parser.add_argument('--port', default='disting NT', help='MIDI port name')
    parser.add_argument('--slot', type=int, default=0, help='Slot number (0-31)')
    parser.add_argument('--list-ports', action='store_true', help='List available MIDI ports')
    parser.add_argument('--wake', action='store_true', help='Send wake message to device')
    
    args = parser.parse_args()
    
    editor = DistingNTEditor()
    
    if args.list_ports:
        in_ports, out_ports = editor.midi.list_ports()
        print("Input ports:", in_ports)
        print("Output ports:", out_ports)
        return
        
    if not editor.connect(args.port):
        print(f"Failed to connect to {args.port}")
        return
        
    editor.current_slot = args.slot
    
    if args.wake:
        editor._send_wake()
        print("Wake message sent")

if __name__ == "__main__":
    main() 