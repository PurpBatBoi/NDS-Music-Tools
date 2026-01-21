import sys
import os
import csv
import traceback
import ndspy.soundBank
from ndspy.soundBank import Instrument, NoteDefinition, NoteType

# ==========================================
# CONFIGURATION
# This defines which SWAR IDs are linked to the SBNK.
# Since we removed the selector, the script defaults to using
# the FIRST item in this list (Slot 0) for all notes.
WAVE_ARCHIVE_IDS = [0, 1, 2, 3] 
# ==========================================

def parse_csv_to_sbnk(csv_path, output_path):
    print(f"Reading: {os.path.basename(csv_path)}")
    
    inst_groups = {}
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        if not reader.fieldnames: raise ValueError("CSV is empty.")
        if 'InstID' not in reader.fieldnames: raise ValueError("Missing 'InstID' column.")

        for row_idx, row in enumerate(reader):
            # Skip empty rows or comments
            if not row['InstID'] or row['InstID'].strip() == '' or row['InstID'].startswith('#'): continue
            try:
                inst_id = int(row['InstID'])
            except ValueError:
                continue

            if inst_id not in inst_groups:
                inst_groups[inst_id] = []
            inst_groups[inst_id].append(row)

    sbnk = ndspy.soundBank.SBNK()
    sbnk.waveArchiveIDs = WAVE_ARCHIVE_IDS
    
    max_id = max(inst_groups.keys()) if inst_groups else -1
    final_instruments = [None] * (max_id + 1)

    for inst_id, rows in inst_groups.items():
        if not rows: continue
        
        inst_type_str = rows[0]['Type'].lower().strip().replace(" ", "")
        print(f"  -> Processing Inst {inst_id} ({inst_type_str})...")

        # --- NULL ---
        if inst_type_str == 'null':
            final_instruments[inst_id] = None

        # --- SIMPLE / PSG ---
        elif inst_type_str in ['simple', 'psg', 'pcm']:
            row = rows[0]
            note_def = create_note_def(row)
            final_instruments[inst_id] = ndspy.soundBank.SingleNoteInstrument(note_def)

        # --- REGIONAL ---
        elif inst_type_str == 'regional':
            try:
                sorted_rows = sorted(rows, key=lambda r: int(r['KeyMax']) if r['KeyMax'] else 127)
            except ValueError:
                print(f"     [Error] Inst {inst_id}: Invalid KeyMax.")
                continue

            regions = []
            for row in sorted_rows:
                key_max = int(row['KeyMax']) if row['KeyMax'] else 127
                note_def = create_note_def(row)
                regions.append(ndspy.soundBank.RegionalInstrument.Region(key_max, note_def))
            
            if regions and regions[-1].lastPitch < 127:
                regions[-1].lastPitch = 127

            final_instruments[inst_id] = ndspy.soundBank.RegionalInstrument(regions)

        # --- RANGE (DRUMS) ---
        elif inst_type_str == 'range':
            keys_all = []
            valid_rows = []
            for r in rows:
                if r['KeyMin'] and r['KeyMax']:
                    keys_all.append(int(r['KeyMin']))
                    keys_all.append(int(r['KeyMax']))
                    valid_rows.append(r)
            
            if not keys_all:
                print(f"     [Error] Inst {inst_id} (Range) has no valid KeyMin/KeyMax.")
                continue

            min_key = min(keys_all)
            max_key = max(keys_all)
            
            key_map = {}
            for r in valid_rows:
                k_start = int(r['KeyMin'])
                k_end = int(r['KeyMax'])
                if k_end < k_start: k_end = k_start
                for k in range(k_start, k_end + 1):
                    key_map[k] = r

            note_defs = []
            for k in range(min_key, max_key + 1):
                if k in key_map:
                    note_defs.append(create_note_def(key_map[k]))
                else:
                    # GAP (Silence)
                    dummy = ndspy.soundBank.NoteDefinition()
                    dummy.sustain = 0 
                    dummy.pitch = 60
                    note_defs.append(dummy)
            
            final_instruments[inst_id] = ndspy.soundBank.RangeInstrument(min_key, note_defs)

    sbnk.instruments = final_instruments
    
    print(f"Writing: {os.path.basename(output_path)}")
    sbnk.saveToFile(output_path)
    print("Done!")

def create_note_def(row):
    def get_int(key, default):
        val = row.get(key, '')
        if val is None or val.strip() == '': return default
        try: return int(val)
        except ValueError: return default
            
    n_type_raw = row.get('NoteType', 'PCM').upper()
    n_type = NoteType.PCM
    if 'SQUARE' in n_type_raw or 'PSG' in n_type_raw:
        if 'NOISE' in n_type_raw: n_type = NoteType.PSG_WHITE_NOISE
        else: n_type = NoteType.PSG_SQUARE_WAVE
    
    wave_id = get_int('WaveID', 0)
    
    nd = NoteDefinition()
    nd.type = n_type
    
    if n_type == NoteType.PCM:
        nd.waveID = wave_id
        # ALWAYS Default to Slot 0 (The first SWAR)
        nd.waveArchiveID = 0
    elif n_type == NoteType.PSG_SQUARE_WAVE:
        nd.dutyCycle = wave_id 
        
    nd.pitch = get_int('RootKey', 60)
    nd.attack = get_int('Attack', 127)
    nd.decay = get_int('Decay', 127)
    nd.sustain = get_int('Sustain', 127)
    nd.release = get_int('Release', 127)
    nd.pan = get_int('Pan', 64)
    
    return nd

if __name__ == "__main__":
    print("--- CSV to SBNK ---")
    if len(sys.argv) == 2:
        f = sys.argv[1]
        out = os.path.join(os.path.dirname(f), os.path.splitext(os.path.basename(f))[0] + ".sbnk")
        try:
            parse_csv_to_sbnk(f, out)
            print("\nSUCCESS!")
        except Exception:
            traceback.print_exc()
        input("Press Enter...")
    elif len(sys.argv) == 3:
        parse_csv_to_sbnk(sys.argv[1], sys.argv[2])
    else:
        print("Drag a CSV file onto this script.")
        input()
