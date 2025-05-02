import sys
import time
import threading
import random
from enum import Enum
from typing import List, Optional, Callable, Union

class SpinnerStyle(Enum):
    """Different spinner animation styles"""
    DOTS = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    BRAILLE = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    LINE = ['|', '/', '-', '\\']
    BOUNCE = ['.  ', '.. ', '...', ' ..', '  .', '   ']
    BAR = ['[=   ]', '[==  ]', '[=== ]', '[ ===]', '[  ==]', '[   =]']
    PULSE = ['█■■■■', '■█■■■', '■■█■■', '■■■█■', '■■■■█']
    RADAR = ['◜', '◠', '◝', '◞', '◡', '◟']
    THINKING = ['🤔 ', ' 🤔']
    LOADING = ['⌛ ', ' ⌛']

class CLISpinner:
    """
    A versatile CLI spinner for showing loading animations in terminal applications.
    
    Features:
    - Multiple spinner styles
    - Customizable text and colors
    - Automatic threading
    - Progress reporting
    
    Example:
        ```python
        # Basic usage
        with CLISpinner("Loading..."):
            time.sleep(5)  # Do some work
            
        # With progress
        spinner = CLISpinner("Processing files")
        spinner.start()
        for i in range(10):
            time.sleep(0.5)
            spinner.update_text(f"Processing file {i+1}/10")
        spinner.stop()
        ```
    """
    
    def __init__(
        self, 
        text: str = "Loading...", 
        style: Union[SpinnerStyle, List[str]] = SpinnerStyle.DOTS,
        delay: float = 0.1,
        done_text: str = "Done!",
        stream=sys.stdout
    ):
        """
        Initialize a new CLI spinner.
        
        Args:
            text: Text to display next to the spinner
            style: Animation style to use (SpinnerStyle enum or list of strings)
            delay: Time delay between animation frames (seconds)
            done_text: Text to display when finished
            stream: Output stream (defaults to stdout)
        """
        self.text = text
        self.frames = style.value if isinstance(style, SpinnerStyle) else style
        self.delay = delay
        self.done_text = done_text
        self.stream = stream
        
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._index = 0
        self._last_line_length = 0
        self._has_progress = False
        self._progress = 0
        self._progress_total = 0
    
    def _clear_line(self):
        """Clear the current line in the terminal."""
        self.stream.write('\r' + ' ' * self._last_line_length + '\r')
        self.stream.flush()
    
    def _render_frame(self):
        """Render the current animation frame."""
        with self._lock:
            frame = self.frames[self._index % len(self.frames)]
            self._index += 1
            
            # Format display line
            if self._has_progress and self._progress_total > 0:
                percentage = min(100, max(0, int((self._progress / self._progress_total) * 100)))
                line = f"{frame} {self.text} [{percentage}%]"
            else:
                line = f"{frame} {self.text}"
                
            # Update line
            self._clear_line()
            self.stream.write(line)
            self.stream.flush()
            self._last_line_length = len(line)
    
    def _spin(self):
        """Main animation loop."""
        while not self._stop_event.is_set():
            self._render_frame()
            time.sleep(self.delay)
    
    def start(self):
        """Start the spinner animation in a separate thread."""
        if self._thread is not None:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin)
        self._thread.daemon = True
        self._thread.start()
        return self
    
    def stop(self, show_done=True):
        """
        Stop the spinner animation.
        
        Args:
            show_done: Whether to show the done message
        """
        if self._thread is None:
            return
        
        self._stop_event.set()
        self._thread.join()
        self._thread = None
        
        self._clear_line()
        if show_done:
            self.stream.write(f"{self.done_text}\n")
            self.stream.flush()
    
    def update_text(self, text: str):
        """
        Update the spinner text.
        
        Args:
            text: New text to display
        """
        with self._lock:
            self.text = text
    
    def set_progress(self, current: int, total: int):
        """
        Set progress values for the spinner.
        
        Args:
            current: Current progress value
            total: Total progress value
        """
        with self._lock:
            self._has_progress = True
            self._progress = current
            self._progress_total = total
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop(show_done=exc_type is None)

class RandomSpinner(CLISpinner):
    """A spinner that randomly selects its style at initialization."""
    
    def __init__(self, text: str = "Loading...", **kwargs):
        style = random.choice(list(SpinnerStyle))
        super().__init__(text=text, style=style, **kwargs)

# Example usage when running this file directly
if __name__ == "__main__":
    # Test different spinner styles
    for style in SpinnerStyle:
        print(f"Testing {style.name} style:")
        spinner = CLISpinner(f"Loading with {style.name}", style=style)
        spinner.start()
        time.sleep(2)
        spinner.stop()
    
    # Test with progress
    spinner = CLISpinner("Downloading files")
    spinner.start()
    for i in range(10):
        spinner.set_progress(i, 10)
        spinner.update_text(f"Downloading file {i+1}/10")
        time.sleep(0.5)
    spinner.stop()
    
    # Test with context manager
    with CLISpinner("Processing data", style=SpinnerStyle.BRAILLE) as spinner:
        for i in range(5):
            time.sleep(0.5)
            spinner.update_text(f"Step {i+1}/5 completed")
    
    print("All spinners tested!") 