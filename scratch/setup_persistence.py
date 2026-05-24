import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import checkpointer

if __name__ == "__main__":
    print("Setting up Postgres checkpointer tables...")
    try:
        checkpointer.setup()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
