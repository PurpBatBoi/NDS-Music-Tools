#!/usr/bin/env python3
"""
SWAV to SWAR Bundler - Numerical Indexing
Sorts files based on the leading number (e.g., 0_, 1_, 10_) 
to ensure the SWAR index matches your SBNK definitions.
"""

import sys
import os
from pathlib import Path
import re

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
    current_folder = Path(__file__).parent.resolve()
    folder_name = current_folder.name
    output_filename = current_folder / f"newSND-bank.swar" # Matches your screenshot name

    print(f"--- SWAV to SWAR Bundler (Fixed Indexing) ---")
    print(f"Working directory: {current_folder}")

    # 1. Find all .swav files
    swav_files = list(current_folder.glob("*.swav"))

    if not swav_files:
        print("\n[!] No .swav files found in this folder.")
    else:
        # 2. Numerical Sort Logic
        # This function extracts the first group of digits from the filename
        def get_leading_number(path):
            match = re.search(r'^(\+?\d+)', path.name)
            return int(match.group(1)) if match else 999

        # Sort based on the actual integer value (10 comes AFTER 2)
        swav_files.sort(key=get_leading_number)
        
        print(f"\nSorting {len(swav_files)} files by leading number...")
        print("-" * 45)
        print(f"{'INDEX':<8} | {'FILENAME':<25}")
        print("-" * 45)

        swav_objects = []
        loaded_count = 0

        # 3. Load files and print verification table
        for i, f in enumerate(swav_files):
            try:
                # This visual check ensures your SBNK links will work
                print(f"SWAR[{i}]   <-- {f.name}")
                
                swav = ndspy.soundWave.SWAV.fromFile(str(f))
                swav_objects.append(swav)
                loaded_count += 1
            except Exception as e:
                print(f"    [!] Failed to load {f.name}: {e}")

        # 4. Save SWAR
        if loaded_count > 0:
            try:
                print("-" * 45)
                print(f"Packing {loaded_count} waves into archive...")
                
                swar = ndspy.soundWaveArchive.SWAR.fromWaves(swav_objects)
                swar.saveToFile(str(output_filename))
                
                print(f"\n[SUCCESS] Created: {output_filename.name}")
                print(f"Your SBNK instruments should now map correctly to these IDs.")
            except Exception as e:
                print(f"\n[!] Error saving SWAR file: {e}")
        else:
            print("\n[!] No valid files to create archive.")

    print("\n" + "="*45)
    input("Done. Press Enter to exit...")

if __name__ == "__main__":
    main()
