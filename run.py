import sys
import os

# Add src to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
from src.main import main_loop

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal Error: {e}")
