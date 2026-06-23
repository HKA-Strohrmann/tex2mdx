import re
from pathlib import Path

from . import ui


#* To add a new rule, just drop it in this list.*
# Every rule takes the text and returns a tuple: (modified_text, number_of_changes)
FormatRule = Callable[[str], Tuple[str, int]]
FORMATTING_PIPELINE: list[FormatRule] = [

]
def process_tex(content: str) -> str:
    """Run all registered formatting steps sequentially on the LaTeX code."""

    for rule in FORMATTING_PIPELINE:        
        content, changes = rule(content)

        ui.console.print(f"[dim]Rule '{rule.__name__}' applied {changes} changes.[/dim]")

    return content