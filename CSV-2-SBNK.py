import sys
import os
import csv
import traceback
import ndspy.soundBank
from ndspy.soundBank import Instrument, NoteDefinition, NoteType

# ==========================================
# CONFIGURATION
# ==========================================
# The list of SWAR IDs this SBNK uses.
# If your sound bank uses WaveArchive 0 and 1, leave as [0, 1].
WAVE_ARCHIVE_IDS = [0, 1] 
# ==========================================

def parse_csv_to_sbnk(csv_path, output_path):
    print(f"Reading: {os.path.basename(csv_path)}")
    
    # 1. Read CSV into memory grouped by Instrument ID
    inst_groups = {}
    
    # encoding='utf-8-sig' handles the BOM that Excel sometimes adds to CSVs
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        # Verify Headers
        required_headers = ['InstID', 'Type']
        if not reader.fieldnames:
            raise ValueError("CSV is empty or unreadable.")
        for h in required_headers:
            if h not in reader.fieldnames:
                raise ValueError(f"Missing required column: '{h}'. Check your spelling!")

        for row_idx, row in enumerate(reader):
            # Skip empty lines or lines without an ID
            if not row['InstID'] or row['InstID'].strip() == '': 
                continue
            
            try:
                inst_id = int(row['InstID'])
            except ValueError:
                print(f"Warning: Row {row_idx+2} has invalid InstID '{row['InstID']}'. Skipping.")
                continue

            if inst_id not in inst_groups:
                inst_groups[inst_id] = []
            inst_groups[inst_id].append(row)

    # 2. Initialize SBNK
    sbnk = ndspy.soundBank.SBNK()
    sbnk.waveArchiveIDs = WAVE_ARCHIVE_IDS
    
    # Prepare list for instruments (indices must match ID)
    max_id = max(inst_groups.keys()) if inst_groups else -1
    final_instruments = [None] * (max_id + 1)

    # 3. Process each group
    for inst_id, rows in inst_groups.items():
        if not rows: continue
        
        # Determine Type from the first row of the group
        inst_type_str = rows[0]['Type'].lower().strip()
        print(f"  -> Processing Instrument {inst_id} ({inst_type_str})...")

        if inst_type_str == 'simple' or inst_type_str == 'psg':
            # --- SIMPLE / PSG ---
            row = rows[0]
            note_def = create_note_def(row)
            final_instruments[inst_id] = ndspy.soundBank.SingleNoteInstrument(note_def)

        elif inst_type_str == 'regional':
            # --- REGIONAL (Splits) ---
            # Sort by KeyMax to ensure correct order
            try:
                sorted_rows = sorted(rows, key=lambda r: int(r['KeyMax']))
            except ValueError:
                print(f"     [Error] Instrument {inst_id} has an invalid KeyMax value. Check CSV.")
                continue

            regions = []
            for row in sorted_rows:
                key_max = int(row['KeyMax'])
                note_def = create_note_def(row)
                regions.append(ndspy.soundBank.RegionalInstrument.Region(key_max, note_def))
            
            # Validity check: Last region must end at 127
            if regions and regions[-1].lastPitch < 127:
                print(f"     [Fix] Extending last region to 127.")
                regions[-1].lastPitch = 127

            final_instruments[inst_id] = ndspy.soundBank.RegionalInstrument(regions)

        elif inst_type_str == 'range':
            # --- RANGE (Drum Kit) ---
            keys = [int(r['KeyMin']) for r in rows]
            min_key = min(keys)
            max_key = max(keys)
            
            # Map Key -> Row Data
            key_map = {int(r['KeyMin']): r for r in rows}
            
            note_defs = []
            for k in range(min_key, max_key + 1):
                if k in key_map:
                    note_defs.append(create_note_def(key_map[k]))
                else:
                    # Create a silent dummy note for gaps
                    dummy = ndspy.soundBank.NoteDefinition()
                    dummy.sustain = 0 # Silent
                    note_defs.append(dummy)
            
            final_instruments[inst_id] = ndspy.soundBank.RangeInstrument(min_key, note_defs)

    sbnk.instruments = final_instruments
    
    print(f"Writing: {os.path.basename(output_path)}")
    sbnk.saveToFile(output_path)
    print("Done!")

def create_note_def(row):
    """Helper to convert a CSV row dict into an ndspy NoteDefinition"""
    
    def get_int(key, default):
        val = row.get(key, '')
        if val is None or val.strip() == '':
            return default
        try:
            return int(val)
        except ValueError:
            return default
            
    n_type_str = row.get('NoteType', 'PCM').upper()
    
    # Determine Type
    n_type = NoteType.PCM
    if 'SQUARE' in n_type_str: n_type = NoteType.PSG_SQUARE_WAVE
    elif 'NOISE' in n_type_str: n_type = NoteType.PSG_WHITE_NOISE
    
    # For PSG Square, WaveID column acts as Duty Cycle
    wave_id = get_int('WaveID', 0)
    
    nd = NoteDefinition()
    nd.type = n_type
    
    if n_type == NoteType.PCM:
        nd.waveID = wave_id
    elif n_type == NoteType.PSG_SQUARE_WAVE:
        nd.dutyCycle = wave_id # Alias
        
    nd.pitch = get_int('RootKey', 60)
    nd.attack = get_int('Attack', 127)
    nd.decay = get_int('Decay', 127)
    nd.sustain = get_int('Sustain', 127) # 0-127 Volume level
    nd.release = get_int('Release', 127)
    nd.pan = get_int('Pan', 64)
    
    return nd

if __name__ == "__main__":
    print("--- CSV to SBNK Converter ---")
    
    input_file = None
    output_file = None
    pause_at_end = False

    # Scenario 1: Drag and Drop (1 argument)
    if len(sys.argv) == 2:
        input_file = sys.argv[1]
        # Automatically name the output file
        folder = os.path.dirname(input_file)
        name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(folder, name + ".sbnk")
        pause_at_end = True # Keep window open so user sees result

    # Scenario 2: Command Line (2 arguments)
    elif len(sys.argv) == 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        pause_at_end = False

    # Scenario 3: No arguments (Double clicked script)
    else:
        print("Usage: Drag a CSV file onto this script.")
        print("OR run: python csv2sbnk.py <input.csv> <output.sbnk>")
        input("Press Enter to exit...")
        sys.exit()

    # Run the conversion
    try:
        parse_csv_to_sbnk(input_file, output_file)
        print("\nSUCCESS!")
    except Exception as e:
        print("\nERROR OCCURRED:")
        traceback.print_exc()
    
    if pause_at_end:
        print("\nPress Enter to close this window...")
        input()
