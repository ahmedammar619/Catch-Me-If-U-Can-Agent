#!/usr/bin/env python3
"""
Run script for the Catch Me If U Can agent
"""

import os
import sys
import argparse
from pathlib import Path

# Get the current directory and add it to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Catch Me If U Can monitoring agent")
    parser.add_argument("--safe-mode", action="store_true", help="Run in safe mode without ML models")
    parser.add_argument("--no-visualization", action="store_true", help="Run without visualization")
    args = parser.parse_args()

    # Import the Agent class
    from backend.agent import Agent

    print("Starting Catch Me If U Can Agent...")
    
    # Create agent with visualization enabled unless disabled via arg
    agent = Agent(show_visualization=not args.no_visualization, safe_mode=args.safe_mode)
    
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\nStopping agent due to keyboard interrupt...")
    except Exception as e:
        print(f"\nError running agent: {e}")
    finally:
        agent.stop()
        print("Agent stopped.") 

if __name__ == "__main__":
    main() 