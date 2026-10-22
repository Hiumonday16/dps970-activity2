# conftest.py is loaded automatically by pytest before the tests run.
# It adds the project root to Python's import path so the tests can do
# "import connect4" no matter which folder pytest is started from.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
