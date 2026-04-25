import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

main_script = Path(__file__).parent / 'src' / 'main.py'
result = subprocess.run([sys.executable, str(main_script)])
sys.exit(result.returncode)
