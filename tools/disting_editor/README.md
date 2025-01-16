# Disting NT Editor

## Version History

### v1.1 - 2024-01-15
Added preset name reading functionality:
- Implemented preset name request command (0x41)
- Added proper parsing of preset name responses
- Fixed SysEx message handling to match WebUI behavior
- Added debug logging for preset name messages
- New example script: `get_preset_name.py`

### v1.0 - 2024-01-15
Initial implementation of MIDI communication layer and algorithm listing functionality.

#### Features
- MIDI Interface implementation for communicating with Disting NT
- SysEx message handling for device communication
- Algorithm listing functionality
  - Retrieves and displays all available algorithms
  - Supports both short names and full algorithm names
  - Proper parsing of SysEx messages for algorithm information

#### Command Line Tools
- `list_algorithms.py`: Lists all available algorithms on the Disting NT
  ```bash
  # Basic usage
  python disting_nt/examples/list_algorithms.py
  
  # Show short names alongside full names
  python disting_nt/examples/list_algorithms.py --show-short-names
  
  # Enable verbose output (info or debug level)
  python disting_nt/examples/list_algorithms.py -v info
  python disting_nt/examples/list_algorithms.py -v debug
  ```

#### Technical Details
- SysEx Message Format documented in code
- Robust error handling for MIDI communication
- Debug logging support for troubleshooting
- Cross-platform MIDI support via python-rtmidi

#### Requirements
- Python 3.x
- python-rtmidi

#### Project Structure
