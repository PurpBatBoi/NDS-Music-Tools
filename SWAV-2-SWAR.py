#!/usr/bin/env python3
"""
Simple SWAV to SWAR Bundler
Place this script in a folder with .swav files and run it.
"""

import sys
import os
from pathlib import Path

# --- Dependency Check ---
try:
    import ndspy.soundWave
    import ndspy.soundWaveArchive
except ImportError:
    print("CRITICAL ERROR: NDSpy is not installed.")
    print("Please open cmd/terminal and run: pip install ndspy")
    input("Press Enter to exit...")
    sys.exit(1)

def main():
    # 1. Determine the folder where this script is sitting
    current_folder = Path(__file__).parent.resolve()
    folder_name = current_folder.name
    output_filename = current_folder / f"{folder_name}.swar"

    print(f"--- SWAV to SWAR Bundler ---")
    print(f"Working directory: {current_folder}")

    # 2. Find all .swav files
    swav_files = list(current_folder.glob("*.swav"))

    if not swav_files:
        print("\n[!] No .swav files found in this folder.")
        print("    Make sure you converted your .wav files to .swav first.")
    else:
        # 3. Sort files Alphabetically (A-Z)
        # This ensures Horn_54 comes before Horn_57
        swav_files.sort(key=lambda x: x.name)
        
        print(f"\nFound {len(swav_files)} files. Sorting by name...")

        # Prepare list for NDSpy
        swav_objects = []
        loaded_count = 0

        # 4. Load files
        print("-" * 40)
        for i, f in enumerate(swav_files):
            try:
                # Print index and name so user can verify order
                print(f"[{i}] Adding: {f.name}")
                swav = ndspy.soundWave.SWAV.fromFile(str(f))
                swav_objects.append(swav)
                loaded_count += 1
            except Exception as e:
                print(f"    [!] Failed to load {f.name}: {e}")

        # 5. Save SWAR
        if loaded_count > 0:
            try:
                print("-" * 40)
                print(f"Creating SWAR file with {loaded_count} waves...")
                
                swar = ndspy.soundWaveArchive.SWAR.fromWaves(swav_objects)
                swar.saveToFile(str(output_filename))
                
                print(f"\n[SUCCESS] Created: {output_filename.name}")
                print(f"Location: {output_filename}")
            except Exception as e:
                print(f"\n[!] Error saving SWAR file: {e}")
        else:
            print("\n[!] No valid files to create archive.")

    # 6. Keep window open
    print("\n" + "="*40)
    input("Done. Press Enter to exit...")

if __name__ == "__main__":
    main()
