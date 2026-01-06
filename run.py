import sys
from pathlib import Path
import asyncio

# Add src to python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from src.main import main_loop

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal Error: {e}")
