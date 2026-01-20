### This guide details how to format your Excel spreadsheet to work with the Python script. The script relies on specific headers and values to generate the Nintendo DS Sound Bank correctly.
---
# 1. Setting Up Excel

1.  Open a blank Excel workbook.
2.  **Row 1** must contain the **Headers**. These are case-sensitive (based on the script provided).
3.  Copy and paste this exact list into the first row, starting at cell **A1**:

    | A | B | C | D | E | F | G | H | I | J | K | L | M |
    | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
    | **InstID** | **Type** | **KeyMin** | **KeyMax** | **NoteType** | **WaveID** | **RootKey** | **Attack** | **Decay** | **Sustain** | **Release** | **Pan** | **Comment** |

4.  **Save the file:** When you are done editing, go to **File > Save As** and choose **CSV UTF-8 (Comma delimited) (*.csv)**.


# 2. Parameter Reference

Here is what every column does and what values you should put in them.

#### The "Structure" Columns
| Column | Description |
| :--- | :--- |
| **InstID** | **Instrument ID**. A generic number (0, 1, 2...) to identify the instrument. <br>• Keep rows with the same ID together.<br>• IDs don't have to be sequential (you can skip ID 5), but they should generally start at 0. |
| **Type** | **The Instrument Type.** Defines how the game handles the sound.<br>• `Simple`: A single sample.<br>• `Regional`: A melodic instrument split across samples (e.g., Piano).<br>• `Range`: A drum kit or percussion bank.<br>• `PSG`: Uses the internal 8-bit synth |
| **KeyMin** | **Lower Key Limit (0-127).**<br>• **For Drums (Range):** Crucial. This is the specific key the drum plays on.<br>• **For Others:** Mostly ignored by the script, but good for documentation. Set to `0` if unsure. |
| **KeyMax** | **Upper Key Limit (0-127).**<br>• **For Regional:** Crucial. This defines where the "split" ends.<br>• **For Simple/PSG:** Set to `127`. |

#### The "Sound" Columns
| Column | Description |
| :--- | :--- |
| **NoteType** | **Source of the sound.**<br>• `PCM`: Plays a .wav sample from the SWAR (Most common).<br>• `PSG_SQUARE`: Plays an 8-bit square wave.<br>• `PSG_NOISE`: Plays 8-bit white noise. |
| **WaveID** | **The Sample Index.**<br>• **If PCM:** The index number of the sample in your SWAR file (e.g., `0` is the first file, `1` is the second).<br>• **If PSG_SQUARE:** The "Duty Cycle" (Tone). Values `0` to `7`. (0 is thin, 3 is a standard NES-style square, 7 is inverse). |
| **RootKey** | **Base Pitch.** usually `60` (Middle C).<br>• If you recorded your sample playing a C4, put `60` here.<br>• If you recorded a C3, put `48`.<br>• **For Drums:** Usually `60`. Changing this changes the pitch of the drum. |
| **Pan** | **Stereo Position (0-127).**<br>• `0`: Hard Left<br>• `64`: Center<br>• `127`: Hard Right |

#### The "Envelope" (ADSR) Columns
*Nintendo DS envelopes are based on **Rate** (Speed) and **Volume**, not Time.*

| Column | Description | Values |
| :--- | :--- | :--- |
| **Attack** | How fast the sound reaches max volume. | `127` = Instant (Start immediately).<br>`0` = Takes forever to fade in. |
| **Decay** | How fast the sound drops to the Sustain level. | `127` = Instant drop.<br>`0` = Never drops. |
| **Sustain** | **Target Volume Level**. This is NOT time. | `127` = 100% Volume (Max).<br>`0` = Silent.<br>*Used for Decay target.* |
| **Release** | How fast the sound fades out after letting go of the key. | `127` = Cuts off instantly.<br>`0` = Rings out forever. |

---

# 3. How to Setup Specific Instruments

#### A. Standard Sound Effect (`Simple`)
Used for coins, jumps, UI sounds.
*   **Type:** `Simple`
*   **KeyMin/Max:** 0 / 127
*   **Rows:** Only 1 row per InstID.

| InstID | Type | KeyMin | KeyMax | NoteType | WaveID | RootKey | Attack | Decay | Sustain | Release |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | Simple | 0 | 127 | PCM | 5 | 60 | 127 | 127 | 127 | 127 |

#### B. Piano / Violin (`Regional`)
Used for melodic instruments where you have multiple samples (Low, Mid, High) to prevent the "chipmunk effect."
*   **Type:** `Regional`
*   **KeyMax:** This is the most important column here. It defines the split point. The script sorts these automatically, but it's good practice to write them in order in Excel.
*   **Envelope:** Usually, Attack is fast (127) and Release is somewhat slow (e.g., 90) so it doesn't click when you let go.

| InstID | Type | KeyMin | KeyMax | NoteType | WaveID | RootKey | ... |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Regional | 0 | **50** | PCM | 10 | 50 | ... |
| 1 | Regional | 51 | **80** | PCM | 11 | 70 | ... |
| 1 | Regional | 81 | **127** | PCM | 12 | 90 | ... |

*Explanation:* Keys 0-50 play Wave 10. Keys 51-80 play Wave 11. Keys 81-127 play Wave 12.

#### C. Drum Kit (`Range`)
Used for percussion. Every key plays a different sound.
*   **Type:** `Range`
*   **KeyMin:** This tells the script exactly which MIDI note triggers this sound.
*   **KeyMax:** Same as KeyMin.
*   **RootKey:** Keep this at 60 unless you want to pitch-shift the drum.

| InstID | Type | KeyMin | KeyMax | NoteType | WaveID | RootKey | ... |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | Range | **36** | 36 | PCM | 100 | 60 | ... |
| 2 | Range | **38** | 38 | PCM | 101 | 60 | ... |
| 2 | Range | **42** | 42 | PCM | 102 | 60 | ... |

*Explanation:* Key 36 plays Wave 100 (Kick). Key 38 plays Wave 101 (Snare). The script will automatically fill the gap (Key 37) with silence.

---

# 4. Common Excel/Spreadsheet Editor Pitfalls

**1. "General" Number Formatting:**
Sometimes Excel thinks `10, 11` is a date.
*   *Fix:* Select all columns with numbers (InstID, WaveID, etc.), Right Click > **Format Cells** > **Text** or **Number** (with 0 decimal places). This prevents Excel from corrupting your IDs.

**2. CSV Saving:**
Excel loves to lock the file.
*   *Fix:* You must **close** the Excel file before running the Python script, or the script will crash with a "Permission Denied" error.

**3. Case Sensitivity:**
The script looks for `Type` (capital T) and `Simple` (capital S, usually).
*   *Fix:* Stick to the casing used in the headers provided in Section 1.
