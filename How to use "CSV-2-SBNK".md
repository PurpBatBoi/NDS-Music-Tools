This script converts a CSV file into a Nintendo DS Sound Bank (.sbnk). To use it, you must structure your spreadsheet (Excel, LibreOffice, or Google Sheets) with specific headers.

The script groups rows by InstID to determine if an instrument is a single note, a split keyboard (Regional), or a drum kit (Range).

---

# **1. Required Column Headers**
The first row of your spreadsheet **must** contain these exact headers. Capitalization matters.

| Header | Description | Required? |
| :--- | :--- | :--- |
| **InstID** | The instrument number (0–127). | **Yes** |
| **Type** | The instrument type (see Section 2). | **Yes** |
| **NoteType** | `PCM`, `PSG`, or `NOISE`. | No (Defaults to PCM) |
| **WaveID** | The ID of the sample in the SWAR, or Duty Cycle for PSG. | No (Defaults to 0) |
| **RootKey** | The base MIDI note of the sample (original pitch). | No (Defaults to 60/C4) |
| **KeyMin** | Used for **Range** (Drum) instruments only. | Only for `Range` |
| **KeyMax** | Used for **Regional** and **Range** instruments. | Only for `Reg` / `Range` |
| **Attack** | Volume envelope attack (0–127). | No (Defaults to 127) |
| **Decay** | Volume envelope decay (0–127). | No (Defaults to 127) |
| **Sustain** | Volume envelope sustain level (0–127). | No (Defaults to 127) |
| **Release** | Volume envelope release (0–127). | No (Defaults to 127) |
| **Pan** | Panning (0 = Left, 64 = Center, 127 = Right). | No (Defaults to 64) |

---

# **2. Instrument Types (The `Type` Column)**
The text in the `Type` column determines how the script processes the rows for that Instrument ID.

#### **A. Simple (or PCM)**
*   **Use for:** Standard melodic instruments consisting of a single sample stretched across the keyboard.
*   **Setup:** One row per InstID.
*   **Key Columns:** `InstID`, `Type`, `WaveID`, `RootKey`.

#### **B. Regional**
*   **Use for:** Instruments that change samples based on pitch (e.g., a Piano with low, mid, and high samples).
*   **Setup:** Multiple rows sharing the same `InstID`.
*   **Key Columns:** `KeyMax`.
*   **Logic:** The script sorts rows by `KeyMax`. The sample will play for all notes up to and including that KeyMax.
    *   *Example:* Row A has `KeyMax` 60. Row B has `KeyMax` 127. Notes 0-60 play Row A; notes 61-127 play Row B.

#### **C. Range**
*   **Use for:** Drum kits or Sound Effects collections where every key plays a specific sound without pitch shifting.
*   **Setup:** Multiple rows sharing the same `InstID`.
*   **Key Columns:** `KeyMin`, `KeyMax`.
*   **Logic:**
    *   You define a specific range for a sample (e.g., `KeyMin`: 36, `KeyMax`: 36 for a Kick drum on C2).
    *   **Gaps:** If you skip keys between ranges (e.g., define 36 and 38, but skip 37), the script automatically creates a silent "dummy" note for the gap (Key 37).

#### **D. Null**
*   **Use for:** Leaving an empty slot in the instrument list.
*   **Setup:** `Type` = `null`. Other columns are ignored.

---

# **3. Note Types & WaveIDs**
The `NoteType` column controls whether the sound uses a sample (PCM) or the internal synth (PSG).

| NoteType | Behavior | Usage of `WaveID` Column |
| :--- | :--- | :--- |
| **PCM** | Plays a .wav sample from the SWAR. | The index of the sample inside the SWAR. |
| **PSG** | Plays a Square Wave (Chiptune sound). | **Duty Cycle** (0–7). Defines the "width" of the square wave tone. |
| **NOISE** | Plays White Noise (Percussion/SFX). | Ignored. |

---

# **4. Example Data**

Here is how your spreadsheet data should look (headers must match exactly):

| A      | B        | C      | D      | E        | F      | G      | H       | I      | J     | K       | L       | M   |
| ------ | -------- | ------ | ------ | -------- | ------ | ------ | ------- | ------ | ----- | ------- | ------- | --- |
| InstID | Type     | KeyMin | KeyMax | NoteType | WaveID | RootKey | Attack | Decay | Sustain | Release | Pan | Comment     |
| 0      | Simple   | 0        | 127        | PCM      | 0      | 69      | 110    | 50    | 90      | 115     | 64  | Horn    |
| 1      | Regional | 0       | 60     | PCM      | 4      | 51      | 110    | 50    | 90      | 115     | 64  | Violin  |
| 1      | Regional | 61       | 127    | PCM      | 5      | 69      | 110    | 50    | 90      | 115     | 64  |         |
| 2      | Range    | 36     | 36     | PCM      | 11     | 36      | 127    | 127   | 127     | 60      | 64  | Kick    |
| 2      | Range    | 38     | 38     | PCM      | 13     | 38      | 127    | 127   | 127     | 60      | 64  | Snare   |
| 2      | Range    | 40     | 40     | PCM      | 14     | 40      | 127    | 127   | 127     | 60      | 64  | Hat     |

**Explanation of Example:**
1.  **Inst 0 (Simple):** A "Horn" instrument. It uses a single sample (WaveID 0) stretched across the entire keyboard.
2.  **Inst 1 (Regional):** A "Violin" that splits the keyboard.
    *   Notes **0–60** play WaveID 4 (Low sample).
    *   Notes **61–127** play WaveID 5 (High sample).
3.  **Inst 2 (Range):** A Drum kit.
    *   Key **36** (C2) plays the Kick (WaveID 11).
    *   Key **38** (D2) plays the Snare (WaveID 13).
    *   Key **40** (E2) plays the Hi-Hat (WaveID 14).
    *   *Note:* Any keys not listed (like 37 or 39) will automatically be silent.

---

# **5. Configuration & Saving**

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
