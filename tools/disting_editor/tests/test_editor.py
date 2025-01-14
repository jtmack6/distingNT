import unittest
from unittest.mock import Mock, patch
from src.editor import DistingNTEditor
from src.midi_handler import MIDIHandler

class TestDistingNTEditor(unittest.TestCase):
    def setUp(self):
        self.editor = DistingNTEditor()
        
    def test_validate_sysex_header(self):
        """Test SysEx header validation."""
        # Valid header
        valid_data = [0xF0, 0x00, 0x21, 0x27, 0x6D, 0x00, 0x07, 0xF7]
        self.assertTrue(self.editor._validate_sysex_header(valid_data))
        
        # Invalid header (wrong manufacturer ID)
        invalid_data = [0xF0, 0x01, 0x21, 0x27, 0x6D, 0x00, 0x07, 0xF7]
        self.assertFalse(self.editor._validate_sysex_header(invalid_data))
        
        # Too short
        short_data = [0xF0, 0x00, 0x21]
        self.assertFalse(self.editor._validate_sysex_header(short_data))

    def test_extract_short(self):
        """Test short value extraction from SysEx data."""
        data = [0x01, 0x02, 0x03]  # 14-bit value format
        result = self.editor._extract_short(data)
        expected = (1 << 14) | (2 << 7) | 3
        self.assertEqual(result, expected)

    @patch('src.midi_handler.MIDIHandler')
    def test_connect(self, mock_midi_handler):
        """Test device connection."""
        # Setup mock
        self.editor.midi = mock_midi_handler
        mock_midi_handler.connect.return_value = True
        
        # Test successful connection
        self.assertTrue(self.editor.connect("test port"))
        mock_midi_handler.connect.assert_called_once_with("test port")
        mock_midi_handler.set_callback.assert_called_once()

    def test_handle_preset_name(self):
        """Test preset name handling."""
        # Test normal preset name
        test_name = "Test Preset"
        data = [ord(c) for c in test_name] + [0] + [0x20] * 5
        with patch('builtins.print') as mock_print:
            self.editor._handle_preset_name(data)
            mock_print.assert_called_once_with(f"Preset name: {test_name}")

        # Test empty preset name
        data = [0] + [0x20] * 20
        with patch('builtins.print') as mock_print:
            self.editor._handle_preset_name(data)
            mock_print.assert_called_once_with("Preset name: ")

    def test_send_sysex(self):
        """Test SysEx message sending."""
        self.editor.midi = Mock()
        test_data = [0x07]  # Wake message
        expected_data = (
            self.editor.MANUFACTURER_ID +
            [self.editor.DEVICE_ID, self.editor.sysex_id] +
            test_data
        )
        
        self.editor.send_sysex(test_data)
        self.editor.midi.send_sysex.assert_called_once_with(expected_data)

if __name__ == '__main__':
    unittest.main()