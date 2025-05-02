import sys
import pytest
import threading
import time
import io
from unittest.mock import patch

# Add the parent directory to sys.path
sys.path.insert(0, ".")

from autoFaceFraming.utils.cli_spinner import CLISpinner, SpinnerStyle, RandomSpinner


def test_spinner_init():
    """Test spinner initialization with default values."""
    spinner = CLISpinner()
    assert spinner.text == "Loading..."
    assert spinner.frames == SpinnerStyle.DOTS.value
    assert spinner.delay == 0.1
    assert spinner.done_text == "Done!"
    assert spinner._thread is None
    assert spinner._index == 0


def test_spinner_custom_style():
    """Test spinner with custom style."""
    spinner = CLISpinner(style=SpinnerStyle.BRAILLE)
    assert spinner.frames == SpinnerStyle.BRAILLE.value
    
    custom_frames = ["A", "B", "C"]
    spinner = CLISpinner(style=custom_frames)
    assert spinner.frames == custom_frames


def test_spinner_update_text():
    """Test spinner text update."""
    spinner = CLISpinner()
    spinner.update_text("New text")
    assert spinner.text == "New text"


def test_spinner_progress():
    """Test spinner progress update."""
    spinner = CLISpinner()
    spinner.set_progress(5, 10)
    assert spinner._has_progress is True
    assert spinner._progress == 5
    assert spinner._progress_total == 10


def test_random_spinner():
    """Test random spinner initialization."""
    with patch('random.choice', return_value=SpinnerStyle.DOTS):
        spinner = RandomSpinner()
        assert spinner.frames == SpinnerStyle.DOTS.value


@pytest.mark.skip(reason="This test involves actual rendering which may not work in CI")
def test_spinner_render():
    """Test that spinner renders correctly."""
    # Use StringIO to capture output
    fake_output = io.StringIO()
    
    with CLISpinner("Testing", stream=fake_output) as spinner:
        time.sleep(0.2)  # Let it spin a bit
        
    output = fake_output.getvalue()
    # At minimum should contain the text
    assert "Testing" in output
    

@pytest.mark.skip(reason="This test involves actual rendering which may not work in CI")
def test_spinner_context_manager():
    """Test that spinner works as a context manager."""
    fake_output = io.StringIO()
    
    with CLISpinner("Context test", stream=fake_output):
        pass
        
    output = fake_output.getvalue()
    # Should contain the done message
    assert "Done!" in output


if __name__ == "__main__":
    # Run tests manually
    test_spinner_init()
    test_spinner_custom_style()
    test_spinner_update_text()
    test_spinner_progress()
    test_random_spinner()
    print("All tests passed!") 