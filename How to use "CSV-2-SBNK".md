This script converts a single CSV file into **two** formats simultaneously:
1.  **Nintendo DS Sound Bank (.sbnk)**: For use in NDS ROMs.
2.  **SoundFont 2 (.sf2)**: For use in DAWs (FL Studio, Ableton) or Polyphone.

To use it, you must structure your spreadsheet with specific headers and organize your WAV files correctly.
The script groups rows by InstID to determine if an instrument is a single note, a split keyboard (Regional), or a drum kit (Range).

---

# **1. File Structure Requirement**
For the **SF2** generation to work, you must place your WAV files in a folder named `Samples` located next to your CSV file.

**Naming Convention:**
Files inside the `Samples` folder must start with the **WaveID** (two digits) followed by an underscore.
*   `00_Kick.wav` (Matches WaveID 0)
*   `01_Snare.wav` (Matches WaveID 1)
*   `10_Strings.wav` (Matches WaveID 10)

```text
MyProject/
├── Instruments.csv
├── CSV-2-SBNK-SF2.py
└── Samples/
    ├── 00_Piano.wav
    ├── 01_Violin.wav
    └── ...
```


# **2. Required Column Headers**
The first row of your spreadsheet **must** contain these exact headers. Capitalization of the header names matters.

| Header | Description | Required? |
| :--- | :--- | :--- |
| **InstID** | The instrument number (0–127). | **Yes** |
| **Type** | The instrument type (Simple, Regional, Range). | **Yes** |
| **NoteType** | `PCM`, `PSG`, or `NOISE`. | No (Defaults to PCM) |
| **WaveID** | The ID of the sample (matches filename prefix). | No (Defaults to 0) |
| **RootKey** | The base MIDI note of the sample (original pitch). | No (Defaults to 60/C4) |
| **KeyMin** | Used for **Range** (Drum) instruments only. | Only for `Range` |
| **KeyMax** | Used for **Regional** and **Range** instruments. | Only for `Reg` / `Range` |
| **Attack** | Volume envelope attack (0–127). | No (Defaults to 127) |
| **Decay** | Volume envelope decay (0–127). | No (Defaults to 127) |
| **Sustain** | Volume envelope sustain level (0–127). | No (Defaults to 127) |
| **Release** | Volume envelope release (0–127). | No (Defaults to 127) |
| **Pan** | Panning (0 = Left, 64 = Center, 127 = Right). | No (Defaults to 64) |
| **LOOP** | Force loop behavior (see Section 5). | No (Auto-detects) |

---

# **3. Instrument Types (The `Type` Column)**

#### **A. Simple (or PCM)**
*   **Use for:** Standard melodic instruments consisting of a single sample stretched across the keyboard.
*   **Setup:** One row per InstID.

#### **B. Regional**
*   **Use for:** Instruments that change samples based on pitch (e.g., a Piano with low, mid, and high samples).
*   **Setup:** Multiple rows sharing the same `InstID`, sorted by `KeyMax`.
*   **Logic:** The sample plays for all notes up to and including the `KeyMax`.

#### **C. Range**
*   **Use for:** Drum kits where every key plays a specific sound.
*   **Setup:** Multiple rows sharing the same `InstID`.
*   **Logic:** Defined by `KeyMin` and `KeyMax`. Gaps between ranges automatically create silent notes.

#### **D. Null**
*   **Use for:** Empty slots. Set `Type` = `null`.

---

# **4. Note Types & WaveIDs**
The `NoteType` column controls whether the sound uses a sample (PCM) or the internal synth (PSG).

| NoteType | Behavior | Usage of `WaveID` Column |
| :--- | :--- | :--- |
| **PCM** | Plays a .wav sample from the SWAR. | The index of the sample inside the SWAR. |
| **PSG** | Plays a Square Wave (Chiptune sound). | **Duty Cycle** (0–7). Defines the "width" of the square wave tone. |
| **NOISE** | Plays White Noise (Percussion/SFX). | Ignored. |

---

# **5. Example Data**

| A      | B        | C      | D      | E      | F       | G      | H     | I       | J       | K   | L    |
| ------ | -------- | ------ | ------ | ------ | ------- | ------ | ----- | ------- | ------- | --- | ---- |
| InstID | Type     | KeyMin | KeyMax | WaveID | RootKey | Attack | Decay | Sustain | Release | Pan | LOOP |
| 0      | Simple   | 0      | 127    | 0      | 69      | 110    | 50    | 90      | 115     | 64  | 1    |
| 1      | Regional | 0      | 60     | 4      | 51      | 110    | 50    | 90      | 115     | 64  | Yes  |
| 1      | Regional | 61     | 127    | 5      | 69      | 110    | 50    | 90      | 115     | 64  | Yes  |
| 2      | Range    | 36     | 36     | 11     | 36      | 127    | 127   | 127     | 60      | 64  | No   |
| 2      | Range    | 38     | 38     | 13     | 38      | 127    | 127   | 127     | 60      | 64  | No   |

**Explanation:**
1.  **Inst 0:** Simple instrument using WaveID 0 (`Samples/00_*.wav`). `LOOP` is set to `1`, forcing it to loop.
2.  **Inst 1:** Regional instrument. Low notes use WaveID 4, High notes use WaveID 5.
3.  **Inst 2:** Drum kit. Kick on key 36, Snare on key 38. `LOOP` is `No` (One-shot).

---

# **5. The LOOP Column**
This column controls whether the sample loops or plays as a "One Shot".

| Value | Result |
| :--- | :--- |
| **1**, **Yes**, **True**, **Loop** | **Forced Loop.** The sample will loop continuously while the key is held. |
| **0**, **No**, **False** | **Forced One-Shot.** The sample plays once and stops, ignoring loop points. |
| **(Empty)** | **Auto-Detect.** The script reads the `.wav` file metadata. If the WAV has "smpl" chunk loop points defined, it loops. If not, it is one-shot. |

---

# **6. Configuration & Saving**

1.  **Saving the CSV:**
    *   In Excel/Sheets, go to **File > Export** or **Save As**.
    *   Choose **CSV (Comma delimited)**.
    *   **Important:** The script expects **UTF-8** encoding. If using Excel, choose **CSV UTF-8 (Comma delimited)** if available.

2.  **Running:**
    *   Drag and drop your saved `.csv` file onto the `csv_to_sbnk.py` script.
    *   The `.sbnk` file will appear in the same folder as the CSV.

3. **Case Sensitivity Rules**
    *   Column Headers (Row 1): These are Case-Sensitive.
         *   You **must** use `InstID`, `Type`, `WaveID`, etc.
         *   **Incorrect:** `instid`, `type`, `waveid` (The script will not find them).

   *   Cell Values (Data): These are Not Case-Sensitive.
         *   The script automatically cleans up text data.
         *   `Simple`, `simple`, and `SIMPLE` all work perfectly.
         *   `PCM`, `pcm`, and `Pcm` are all accepted.
