import sys
import os
import csv
import traceback
import struct
import wave
import math
import ndspy.soundBank
from ndspy.soundBank import Instrument, NoteDefinition, NoteType

# ==========================================
# CONFIGURATION
# ==========================================
WAVE_ARCHIVE_IDS = [0, 1, 2, 3] 

# ==========================================
# TUNING CONSTANTS
# ==========================================
# Release: NDS (Linear) -> SF2 (Exponential) requires stretching (~3.1x)
# Decay: Kept 1:1 to preserve punchiness of attack transients
SF2_RELEASE_SCALAR = 1.8

# ==========================================
# TABLES & CONVERSIONS
# ==========================================

ATTACK_TABLE = [
    8606.1, 4756.3, 3339.3, 2594.4, 2130.7, 1807.7, 1573.3, 1401.4,
    1255.5, 1140.9, 1047.1, 963.8, 896.0, 838.7, 786.6, 745.0,
    703.3, 666.8, 630.4, 599.1, 578.3, 547.0, 526.2, 505.3,
    484.5, 468.9, 448.0, 437.6, 416.8, 406.4, 395.9, 385.5,
    369.9, 359.5, 349.0, 338.6, 328.2, 323.0, 312.6, 307.4,
    297.0, 291.7, 286.5, 276.1, 270.9, 265.7, 260.5, 255.3,
    250.1, 244.9, 239.6, 234.4, 229.2, 224.0, 218.8, 213.6,
    213.6, 208.4, 203.2, 203.2, 198.0, 198.0, 192.8, 192.8,
    182.3, 182.3, 177.1, 177.1, 171.9, 171.9, 166.7, 166.7,
    161.5, 161.5, 156.3, 156.3, 151.1, 151.1, 145.9, 145.9,
    145.9, 145.9, 140.7, 140.7, 140.7, 130.2, 130.2, 130.2,
    125.0, 125.0, 125.0, 125.0, 119.8, 119.8, 119.8, 114.6,
    114.6, 114.6, 114.6, 109.4, 109.4, 109.4, 109.4, 109.4,
    104.2, 104.2, 104.2, 104.2, 99.0, 93.8, 88.6, 83.4,
    78.2, 72.9, 67.7, 62.5, 57.3, 52.1, 46.9, 41.7,
    36.5, 31.3, 26.1, 20.8, 15.6, 10.4, 10.4, 0.0
]

MAX_DR_TABLE = [
    481228.8, 160409.6, 96241.6, 68744.0, 53466.4, 43747.6, 37013.6, 32078.8,
    28303.6, 25324.0, 22911.2, 20919.6, 19245.2, 17820.4, 16593.2, 15522.0,
    14580.8, 13748.8, 13005.2, 12334.4, 11736.4, 11190.4, 10691.2, 10238.8,
    9817.6, 9432.8, 9079.2, 8746.4, 8439.6, 8153.6, 7888.4, 7633.6,
    7399.6, 7181.2, 6973.2, 6775.6, 6588.4, 6411.6, 6245.2, 6089.2,
    5938.4, 5792.8, 5657.6, 5527.6, 5402.8, 5283.2, 5174.0, 5064.8,
    4960.8, 4856.8, 4758.0, 4695.6, 4633.2, 4570.8, 4508.4, 4446.0,
    4383.6, 4321.2, 4258.8, 4196.4, 4134.0, 4071.6, 4009.2, 3946.8,
    3884.4, 3822.0, 3759.6, 3692.0, 3629.6, 3567.2, 3504.8, 3442.4,
    3380.0, 3317.6, 3255.2, 3192.8, 3130.4, 3068.0, 3005.6, 2943.2,
    2880.8, 2818.4, 2756.0, 2693.6, 2631.2, 2568.8, 2506.4, 2438.8,
    2376.4, 2314.0, 2251.6, 2189.2, 2126.8, 2064.4, 2002.0, 1939.6,
    1877.2, 1814.8, 1752.4, 1690.0, 1627.6, 1565.2, 1502.8, 1440.4,
    1378.0, 1315.6, 1253.2, 1185.6, 1123.2, 1060.8, 998.4, 936.0,
    873.6, 811.2, 748.8, 686.4, 624.0, 561.6, 499.2, 436.8,
    374.4, 312.0, 249.6, 187.2, 124.8, 62.4, 31.2, 5.2
]

def get_sustain_linear(val):
    return (val / 127.0) ** 2

def get_attack_ms(val):
    return 0.0 if val >= 127 else ATTACK_TABLE[val]

def get_decay_time_hw(decay_val, sustain_val):
    if decay_val >= 127: return 0.0
    max_time = MAX_DR_TABLE[decay_val]
    sus_frac = get_sustain_linear(sustain_val)
    return max_time * (1.0 - sus_frac)

def get_release_time_hw(release_val, sustain_val):
    if release_val >= 127: return 0.0
    max_time = MAX_DR_TABLE[release_val]
    sus_frac = get_sustain_linear(sustain_val)
    return max_time * sus_frac

def get_sustain_db_sf2(val):
    if val >= 127: return 0
    if val == 0: return 1440
    fraction = (val / 127.0) ** 2
    if fraction > 0:
        attenuation = -20 * math.log10(fraction)
    else:
        attenuation = 144.0
    return int(min(max(attenuation * 10, 0), 1440))

def ms_to_timecents(ms):
    if ms <= 0: return -12000
    seconds = ms / 1000.0
    timecents = int(1200 * math.log2(seconds))
    return max(-12000, min(timecents, 8000))

# ==========================================
# SF2 FILE GENERATION
# ==========================================

class SF2Generator:
    def __init__(self, name="NDS_Sound"):
        self.name = name[:256]
        self.samples = []
        self.instruments = []
        self.presets = []
        
    def add_sample_from_wav(self, wav_path, name):
        try:
            loop_start = 0
            loop_end = 0
            found_loop = False
            
            # 1. Parse 'smpl' chunk for loop points
            with open(wav_path, 'rb') as f:
                riff = f.read(4)
                if riff != b'RIFF': return None, False
                file_size = struct.unpack('<I', f.read(4))[0]
                wave_id = f.read(4)
                if wave_id != b'WAVE': return None, False
                
                while f.tell() < file_size + 8:
                    try:
                        chunk_id = f.read(4)
                        if len(chunk_id) < 4: break
                        chunk_size = struct.unpack('<I', f.read(4))[0]
                        chunk_start = f.tell()
                        
                        if chunk_id == b'smpl':
                            f.seek(chunk_start + 28)
                            num_loops = struct.unpack('<I', f.read(4))[0]
                            if num_loops > 0:
                                f.read(4)
                                # Loop info
                                loop_id = struct.unpack('<I', f.read(4))[0]
                                loop_type = struct.unpack('<I', f.read(4))[0]
                                loop_start = struct.unpack('<I', f.read(4))[0]
                                loop_end = struct.unpack('<I', f.read(4))[0]
                                print(f"     [Info] {name}: Found loop points {loop_start}-{loop_end}")
                                found_loop = True
                            break
                        else:
                            f.seek(chunk_start + chunk_size)
                            if chunk_size % 2: f.read(1)
                    except: break
            
            # 2. Read Audio Data (Assumes MONO)
            with wave.open(wav_path, 'rb') as wav:
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                n_frames = wav.getnframes()
                audio_data = wav.readframes(n_frames)
                
                if sample_width != 2:
                    print(f"     [Warning] {name}: 16-bit only, skipping")
                    return None, False
                
                import array
                samples_array = array.array('h')
                samples_array.frombytes(audio_data)
                
                # Sanity check for loop points
                if loop_end == 0 or loop_end >= len(samples_array):
                    loop_end = len(samples_array) - 1
                if loop_start >= loop_end:
                    loop_start = 0
                
                sample = {
                    'name': name[:20],
                    'data': samples_array,
                    'sample_rate': framerate,
                    'original_pitch': 60,
                    'pitch_correction': 0,
                    'loop_start': loop_start,
                    'loop_end': loop_end,
                    'found_loop': found_loop 
                }
                
                self.samples.append(sample)
                return len(self.samples) - 1, found_loop
                
        except Exception as e:
            print(f"     [Error] Failed load {wav_path}: {e}")
            return None, False
    
    def create_instrument(self, name, regions):
        inst = {'name': name[:20], 'regions': regions}
        self.instruments.append(inst)
        return len(self.instruments) - 1
    
    def create_preset(self, name, bank, preset_num, instrument_idx):
        preset = {'name': name[:20], 'bank': bank, 'preset': preset_num, 'instrument_idx': instrument_idx}
        self.presets.append(preset)
    
    def write_sf2(self, output_path):
        with open(output_path, 'wb') as f:
            f.write(b'RIFF')
            riff_size_pos = f.tell()
            f.write(struct.pack('<I', 0))
            f.write(b'sfbk')
            self._write_info_chunk(f)
            self._write_sdta_chunk(f)
            self._write_pdta_chunk(f)
            file_size = f.tell()
            f.seek(riff_size_pos)
            f.write(struct.pack('<I', file_size - 8))
    
    def _write_info_chunk(self, f):
        info_data = b''
        ifil = struct.pack('<HH', 2, 1)
        info_data += b'ifil' + struct.pack('<I', len(ifil)) + ifil
        isng = b'EMU8000\x00'
        info_data += b'isng' + struct.pack('<I', len(isng)) + isng
        inam = (self.name + '\x00').encode('ascii')
        info_data += b'INAM' + struct.pack('<I', len(inam)) + inam
        f.write(b'LIST')
        f.write(struct.pack('<I', len(info_data) + 4))
        f.write(b'INFO')
        f.write(info_data)
    
    def _write_sdta_chunk(self, f):
        smpl_data = b''
        for sample in self.samples:
            smpl_data += sample['data'].tobytes()
        smpl_data += b'\x00' * (46 * 2)
        f.write(b'LIST')
        f.write(struct.pack('<I', len(smpl_data) + 12))
        f.write(b'sdta')
        f.write(b'smpl')
        f.write(struct.pack('<I', len(smpl_data)))
        f.write(smpl_data)
    
    def _write_pdta_chunk(self, f):
        pdta_data = b''
        chunk_writers = [
            (b'phdr', self._build_phdr), (b'pbag', self._build_pbag), 
            (b'pmod', self._build_pmod), (b'pgen', self._build_pgen), 
            (b'inst', self._build_inst), (b'ibag', self._build_ibag),
            (b'imod', self._build_imod), (b'igen', self._build_igen), 
            (b'shdr', self._build_shdr)
        ]
        
        for chunk_id, func in chunk_writers:
            data = func()
            pdta_data += chunk_id + struct.pack('<I', len(data)) + data
            
        f.write(b'LIST')
        f.write(struct.pack('<I', len(pdta_data) + 4))
        f.write(b'pdta')
        f.write(pdta_data)
    
    def _build_phdr(self):
        data = b''
        bag_idx = 0
        for preset in self.presets:
            data += preset['name'].ljust(20, '\x00').encode('ascii')
            data += struct.pack('<HHHLLL', preset['preset'], preset['bank'], bag_idx, 0, 0, 0)
            bag_idx += 1
        data += b'EOP\x00'.ljust(20, b'\x00')
        data += struct.pack('<HHHLLL', 0, 0, bag_idx, 0, 0, 0)
        return data
    
    def _build_pbag(self):
        data = b''
        gen_idx = 0
        for _ in self.presets:
            data += struct.pack('<HH', gen_idx, 0)
            gen_idx += 1
        data += struct.pack('<HH', gen_idx, 0)
        return data
    
    def _build_pmod(self):
        return struct.pack('<HHhHH', 0, 0, 0, 0, 0)
    
    def _build_pgen(self):
        data = b''
        for preset in self.presets:
            data += struct.pack('<HH', 41, preset['instrument_idx'])
        data += struct.pack('<HH', 0, 0)
        return data
    
    def _build_inst(self):
        data = b''
        bag_idx = 0
        for inst in self.instruments:
            data += inst['name'].ljust(20, '\x00').encode('ascii')
            data += struct.pack('<H', bag_idx)
            bag_idx += len(inst['regions'])
        data += b'EOI\x00'.ljust(20, b'\x00')
        data += struct.pack('<H', bag_idx)
        return data
    
    def _build_ibag(self):
        data = b''
        gen_idx = 0
        for inst in self.instruments:
            for _ in inst['regions']:
                data += struct.pack('<HH', gen_idx, 0)
                gen_idx += 9 # 9 Generators per region
        data += struct.pack('<HH', gen_idx, 0)
        return data
    
    def _build_imod(self):
        return struct.pack('<HHhHH', 0, 0, 0, 0, 0)
    
    def _build_igen(self):
        data = b''
        for inst in self.instruments:
            for region in inst['regions']:
                # 17: Pan
                pan_val = int((region['pan'] - 64) * (500 / 64.0))
                data += struct.pack('<Hh', 17, pan_val)
                # 34, 36, 37, 38: ADSR
                # NOTE: Attack and Decay use 1:1 hardware mapping
                # Release is scaled (Linear->Exponential)
                data += struct.pack('<Hh', 34, ms_to_timecents(region['attack']))
                data += struct.pack('<Hh', 36, ms_to_timecents(region['decay']))
                data += struct.pack('<Hh', 37, region['sustain'])
                data += struct.pack('<Hh', 38, ms_to_timecents(region['release']))
                # 43: Key Range
                data += struct.pack('<H', 43) + struct.pack('<BB', region['key_min'], region['key_max'])
                # 53: Sample ID
                data += struct.pack('<Hh', 53, region['sample_idx'])
                # 54: Sample Mode (0=No Loop, 1=Loop)
                loop_val = 1 if region.get('loop_mode', 0) == 1 else 0
                data += struct.pack('<Hh', 54, loop_val)
                # 58: Root Key
                data += struct.pack('<Hh', 58, region['root_key'])
        data += struct.pack('<Hh', 0, 0)
        return data
    
    def _build_shdr(self):
        data = b''
        sample_offset = 0
        for sample in self.samples:
            name = sample['name'].ljust(20, '\x00').encode('ascii')
            data += name
            
            start = sample_offset
            end = sample_offset + len(sample['data'])
            loop_start = start + sample['loop_start']
            # SF2 requirement: End loop is index AFTER the last sample of loop
            loop_end = start + sample['loop_end'] + 1
            
            data += struct.pack('<I', start)
            data += struct.pack('<I', end)
            data += struct.pack('<I', loop_start)
            data += struct.pack('<I', loop_end)
            data += struct.pack('<I', sample['sample_rate'])
            data += struct.pack('<B', sample['original_pitch'])
            data += struct.pack('<b', sample['pitch_correction'])
            data += struct.pack('<H', 0)
            # sfSampleType: ALWAYS 1 (Mono). 
            data += struct.pack('<H', 1) 
            
            sample_offset = end
            
        data += b'EOS\x00'.ljust(20, b'\x00')
        data += struct.pack('<IIIIIBBHH', 0, 0, 0, 0, 0, 0, 0, 0, 0)
        return data

# ==========================================
# MAIN PARSING LOGIC
# ==========================================

def parse_csv_to_sbnk_and_sf2(csv_path, output_sbnk_path, output_sf2_path):
    print(f"Reading: {os.path.basename(csv_path)}")
    
    inst_groups = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or 'InstID' not in reader.fieldnames:
            raise ValueError("Invalid CSV format")
        for row in reader:
            if not row['InstID'] or row['InstID'].startswith('#'): continue
            try:
                inst_id = int(row['InstID'])
                if inst_id not in inst_groups: inst_groups[inst_id] = []
                inst_groups[inst_id].append(row)
            except ValueError: continue

    # SBNK GENERATION (HARDWARE ACCURATE)
    sbnk = ndspy.soundBank.SBNK()
    sbnk.waveArchiveIDs = WAVE_ARCHIVE_IDS
    max_id = max(inst_groups.keys()) if inst_groups else -1
    final_instruments = [None] * (max_id + 1)

    for inst_id, rows in inst_groups.items():
        inst_type = rows[0]['Type'].lower().strip().replace(" ", "")
        print(f"  -> Processing Inst {inst_id} ({inst_type})...")

        if inst_type == 'null':
            final_instruments[inst_id] = None
        elif inst_type in ['simple', 'psg', 'pcm']:
            final_instruments[inst_id] = ndspy.soundBank.SingleNoteInstrument(create_note_def(rows[0]))
        elif inst_type == 'regional':
            sorted_rows = sorted(rows, key=lambda r: int(r['KeyMax']) if r['KeyMax'] else 127)
            regions = [ndspy.soundBank.RegionalInstrument.Region(
                int(r['KeyMax']) if r['KeyMax'] else 127, create_note_def(r)) for r in sorted_rows]
            if regions and regions[-1].lastPitch < 127: regions[-1].lastPitch = 127
            final_instruments[inst_id] = ndspy.soundBank.RegionalInstrument(regions)
        elif inst_type == 'range':
            keys = []
            valid_rows = []
            for r in rows:
                if r['KeyMin'] and r['KeyMax']:
                    keys.extend([int(r['KeyMin']), int(r['KeyMax'])])
                    valid_rows.append(r)
            if keys:
                min_k, max_k = min(keys), max(keys)
                key_map = {}
                for r in valid_rows:
                    for k in range(int(r['KeyMin']), int(r['KeyMax']) + 1):
                        key_map[k] = r
                note_defs = []
                for k in range(min_k, max_k + 1):
                    if k in key_map: note_defs.append(create_note_def(key_map[k]))
                    else: 
                        d = ndspy.soundBank.NoteDefinition()
                        d.pitch = 60
                        note_defs.append(d)
                final_instruments[inst_id] = ndspy.soundBank.RangeInstrument(min_k, note_defs)

    sbnk.instruments = final_instruments
    sbnk.saveToFile(output_sbnk_path)
    print(f"SBNK saved to {output_sbnk_path}")

    # SF2 GENERATION
    csv_dir = os.path.dirname(csv_path)
    samples_dir = os.path.join(csv_dir, "Samples")
    if not os.path.exists(samples_dir):
        print("Samples folder not found, skipping SF2.")
        return

    sf2 = SF2Generator(os.path.splitext(os.path.basename(csv_path))[0])
    sample_map = {} # Maps WaveID to (sf2_index, has_loop_points)

    # Pre-load samples
    for inst_id, rows in inst_groups.items():
        for row in rows:
            wave_id = get_int(row, 'WaveID', 0)
            if wave_id in sample_map: continue
            
            wav_files = [f for f in os.listdir(samples_dir) if f.startswith(f"{wave_id:02d}_") and f.endswith('.wav')]
            if not wav_files: continue
            
            idx, has_loop = sf2.add_sample_from_wav(os.path.join(samples_dir, wav_files[0]), os.path.splitext(wav_files[0])[0])
            if idx is not None:
                sample_map[wave_id] = (idx, has_loop)

    # Build Instruments
    for inst_id, rows in inst_groups.items():
        if not rows: continue
        inst_type = rows[0]['Type'].lower().strip().replace(" ", "")
        inst_name = rows[0].get('Comment', f"Inst{inst_id:03d}")[:20] or f"Inst{inst_id:03d}"
        
        if inst_type == 'null': continue

        sf2_regions = []
        
        # Helper to process a row into a region
        def process_row_for_sf2(row, k_min, k_max):
            wid = get_int(row, 'WaveID', 0)
            if wid not in sample_map: return None
            
            s_idx, s_has_loop = sample_map[wid]
            
            # Loop Logic
            loop_col = row.get('LOOP', '').strip().lower()
            if loop_col in ['1', 'yes', 'true', 'loop']:
                loop_mode = 1
            elif loop_col in ['0', 'no', 'false']:
                loop_mode = 0
            else:
                loop_mode = 1 if s_has_loop else 0
            
            # ADSR CALCULATION 
            decay_raw = get_decay_time_hw(get_int(row, 'Decay', 127), get_int(row, 'Sustain', 127))
            release_raw = get_release_time_hw(get_int(row, 'Release', 127), get_int(row, 'Sustain', 127))

            return {
                'sample_idx': s_idx,
                'key_min': k_min, 'key_max': k_max,
                'root_key': get_int(row, 'RootKey', 60),
                'attack': get_attack_ms(get_int(row, 'Attack', 127)),
                # DECAY: UN-SCALED (Hardware Accurate punch)
                'decay': decay_raw, 
                'sustain': get_sustain_db_sf2(get_int(row, 'Sustain', 127)),
                # RELEASE: SCALED (Linear to Exponential fix)
                'release': release_raw * SF2_RELEASE_SCALAR,
                'pan': get_int(row, 'Pan', 64),
                'loop_mode': loop_mode
            }

        if inst_type in ['simple', 'psg', 'pcm']:
            reg = process_row_for_sf2(rows[0], 0, 127)
            if reg: sf2_regions.append(reg)
            
        elif inst_type == 'regional':
            sorted_rows = sorted(rows, key=lambda r: int(r['KeyMax']) if r['KeyMax'] else 127)
            prev = -1
            for row in sorted_rows:
                km = int(row['KeyMax']) if row['KeyMax'] else 127
                reg = process_row_for_sf2(row, prev + 1, km)
                if reg: sf2_regions.append(reg)
                prev = km
                
        elif inst_type == 'range':
            valid_rows = [r for r in rows if r['KeyMin'] and r['KeyMax']]
            if valid_rows:
                keys = [int(r['KeyMin']) for r in valid_rows] + [int(r['KeyMax']) for r in valid_rows]
                k_map = {}
                for r in valid_rows:
                    for k in range(int(r['KeyMin']), int(r['KeyMax']) + 1):
                        k_map[k] = r
                for k in range(min(keys), max(keys) + 1):
                    if k in k_map:
                        reg = process_row_for_sf2(k_map[k], k, k)
                        if reg: sf2_regions.append(reg)

        if sf2_regions:
            idx = sf2.create_instrument(inst_name, sf2_regions)
            sf2.create_preset(inst_name, 0, inst_id, idx)

    sf2.write_sf2(output_sf2_path)
    print(f"SF2 saved to {output_sf2_path}")
    print("Done!")

def create_note_def(row):
    n_type_raw = row.get('NoteType', 'PCM').upper()
    n_type = NoteType.PCM
    if 'SQUARE' in n_type_raw or 'PSG' in n_type_raw:
        n_type = NoteType.PSG_WHITE_NOISE if 'NOISE' in n_type_raw else NoteType.PSG_SQUARE_WAVE
    nd = NoteDefinition()
    nd.type = n_type
    if n_type == NoteType.PCM:
        nd.waveID = get_int(row, 'WaveID', 0)
        nd.waveArchiveID = 0
    elif n_type == NoteType.PSG_SQUARE_WAVE:
        nd.dutyCycle = get_int(row, 'WaveID', 0)
    nd.pitch = get_int(row, 'RootKey', 60)
    nd.attack = get_int(row, 'Attack', 127)
    nd.decay = get_int(row, 'Decay', 127)
    nd.sustain = get_int(row, 'Sustain', 127)
    nd.release = get_int(row, 'Release', 127)
    nd.pan = get_int(row, 'Pan', 64)
    return nd

def get_int(row, key, default):
    try: return int(row.get(key, default))
    except: return default

if __name__ == "__main__":
    if len(sys.argv) == 2:
        parse_csv_to_sbnk_and_sf2(sys.argv[1], os.path.splitext(sys.argv[1])[0] + ".sbnk", os.path.splitext(sys.argv[1])[0] + ".sf2")
    elif len(sys.argv) == 4:
        parse_csv_to_sbnk_and_sf2(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Usage: Drag CSV file onto script")
    input("Press Enter to exit...")
