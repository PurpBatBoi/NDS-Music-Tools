This document outlines the avaliable feature set SMFconv provides to convert Standard MIDI Files (SMF) for the Nintendo DS, and provides a complete reference for the supported commands.

---
### 1. Note and Pitch
*   **Note On / Note Off:** Fully supported.
    *   Velocity (0-127) is preserved and uses squared value scaling (127 = 100%).
    *   Middle C is represented as `cn4` (Key 60)
*   **Pitch Bend:** Supported.
*   **Program Change:** Supported.

### 2. Control Changes (CC) - Detailed Mapping
The tool maps standard MIDI CCs to specific sound engine commands.

| CC ID | Target Command | Description | Value Range/Notes |
| :--- | :--- | :--- | :--- |
| **1** | `mod_depth` | Sets vibrato depth. | 0-127 (default: 0) |
| **5** | `porta_time` | Sets the speed/time for portamento. | 0-255 (default: 0) |
| **7** | `volume` | Channel volume. | 0-127 (default: 127, squared scaling) |
| **10** | `pan` | Stereo panning. | 0=left, 127=right, 64=center (default: 64) |
| **11** | `volume2` | Expression (secondary volume). | 0-127 (default: 127, squared scaling) |
| **12** | `main_volume` | Master Volume for the Player. | 0-127 (default: 127, squared scaling) |
| **13** | `transpose` | Transposes the key. | Value - 64 (-64 to +63 semitones) |
| **14** | `prio` | Sets channel priority for voice allocation. | 0-127 (default: 64) |
| **16** | `setvar 0` | Sets value in local variable 0. | Used for program communication |
| **17** | `setvar 1` | Sets value in local variable 1. | Used for program communication |
| **18** | `setvar 2` | Sets value in local variable 2. | Used for program communication |
| **19** | `setvar 3` | Sets value in local variable 3. | Used for program communication |
| **20** | `bendrange` | Sets pitch bend range in semitones. | 0-127 (default: 2) |
| **21** | `mod_speed` | Vibrato speed. | 0-127 (default: 16, ~0.4Hz to 50Hz) |
| **22** | `mod_type` | Vibrato waveform type. | 0=pitch, 1=volume, 2=pan |
| **23** | `mod_range` | Vibrato range multiplier. | 0-127 (default: 1) |
| **26** | `mod_delay` | Delay before vibrato starts. | 0-127 (units: sound frames ~5ms) |
| **27** | `mod_delay (×10)` | Extended range modulation delay. | 0-1270 (value × 10) |
| **28** | `sweep_pitch` | Pitch sweep amount. | Value - 64 (-64 to +63) |
| **29** | `sweep_pitch (×24)` | Extended range sweep pitch. | (Value - 64) × 24 (-1536 to +1512) |
| **65** | `porta_on/off` | Portamento switch. | ≥64 = On, <64 = Off |
| **84** | `porta` | Portamento start point. | 0-127 (MIDI note number) |
| **85** | `attack` | Envelope Attack rate. | 0-127 |
| **86** | `decay` | Envelope Decay rate. | 0-127 |
| **87** | `sustain` | Envelope Sustain level. | 0-127 |
| **88** | `release` | Envelope Release rate. | 0-127 |
| **89** | `loop_start` | Sets a loop starting point. | Value 0 for individual track loops |
| **90** | `loop_end` | Jumps back to loop start. | Arbitrary value for individual track loops |

### 3. Meta Events: Text Command Targeting

**Text Events (`FF 01`)** allow you to embed raw engine commands directly into your MIDI file. Since standard MIDI doesn't support features like randomization or logic, you use these text events to "speak" directly to the NITRO engine.

You can control exactly which tracks receive these commands by adding a specific prefix to your text string.

#### For Reaper Users
Insert these commands in the **MIDI Editor** using the **Text Events** lane.

*   **Target ALL Tracks (`text_all:`):**
    Broadcasts the command to every active track simultaneously. This is the best way to apply global settings like polyphony or master volume.
    *   *Example:* `text_all: notewait_off` (Enables polyphony for the entire song).

*   **Target Specific Track (`text_XX:`):**
    Sends the command to a specific Track ID (00–15), regardless of which MIDI lane the event is physically placed on.
    *   **Rule:** `Track ID = MIDI Channel - 1`
    *   *Example:* `text_00: volume 127` (Sets volume for **MIDI Ch 1**).
    *   *Example:* `text_01: volume 127` (Sets volume for **MIDI Ch 2**).

*   **Target Current Track (No Prefix):**
    Sends the command only to the specific track where the text event is placed.
    *   *Example:* `call_seq` (Calls a subroutine only for this instrument).

#### For Domino Users
In Domino, you can insert these commands directly into the Event List.
1.  Right-click in the **Event List** pane.
2.  Select **Insert > Meta Event > Text Event**.
3.  Type the command (e.g., `loop_start`) into the data field.
    *   *Note:* Domino handles track separation natively. If you place a text event on "Track 1" in Domino, it automatically applies to that track without needing a prefix, unless you specifically want to broadcast to `text_all:`.

---

### 4. Advanced Looping & Logic (Via Text Events)

The SMFconv converter parses specific text characters to handle looping logic that standard MIDI cannot express.

*   **Global Loops:**
    *   Insert a text event containing `[` to generate a `_LoopStart` label at that position.
    *   Insert a text event containing `]` to generate a `jump _LoopStart` command at that position.

> **Note:** This creates a global loop point for the entire sequence. For track-specific looping (looping just the drums while the melody continues), use the `loop_start` / `loop_end` commands described in the reference below.

---

### 5. Text-Only Command Reference

The following commands provide advanced logic, flow control, and randomization. They cannot be triggered by knobs or CCs and **must** be entered via Text Events.

#### A. Setup & Modes
*   **`alloctrack mask`**
    *   **Requirement:** This must be the very first command in the sequence (Time 1.1.00).
    *   Allocates memory for the tracks you intend to use via a hex bitmask.
*   **`opentrack no, label`**
    *   Starts a parallel track number (`no`) beginning at a specific text `label`.
*   **`notewait_off` / `notewait_on`**
    *   **Off:** Enables **Polyphony**. The sequencer plays a note and immediately processes the next command without waiting. Essential for playing chords on a single track.
    *   **On:** (Default) Monophonic behavior. The sequencer waits for the note duration to complete.
*   **`tieon` / `tieoff`**
    *   **On:** Enables tie mode. Consecutive notes slide pitch without re-triggering the envelope attack (Legato).

> **Example: Setup**
> ```text
> alloctrack 0xFFFF      ; Allocate all 16 tracks
> text_all: notewait_off ; Enable chords/polyphony globally
> ```

#### B. Flow Control (Jumps & Subroutines)
*   **`jump label`**
    *   Performs an unconditional jump to a specific marker or label. Commonly used for infinite loops.
*   **`call label`**
    *   Jumps to a label to run a "subroutine" (a reusable musical pattern).
*   **`ret`**
    *   Returns from a subroutine, resuming playback at the point where `call` was used.

> **Example: Infinite Loop**
> ```text
> my_loop:
> ... (music notes) ...
> jump my_loop           ; Jumps back to start
> ```

#### C. Randomization (`_r`)
Most standard commands have a randomized variation denoted by the `_r` suffix. When executed, the engine picks a random value between `min` and `max`.

* Table of supported randomized commands:

| Commands      |               |             |             |
| ------------- | ------------- | ----------- | ----------- |
| wait_r        | prg_r         | volume_r    | volume2_r   |
| main_volume_r | pitchbend_r   | pan_r       | transpose_r |
| porta_time_r  | sweep_pitch_r | mod_depth_r | mod_speed_r |
| attack_r      | decay_r       | sustain_r   | release_r   |
| mod_delay_r   | loop_start_r  | setvar_r    | addvar_r    |
| subvar_r      | mulvar_r      | divvar_r    | shiftvar_r  |
| randvar_r     | cmp_eq_r      | cmp_ge_r    | cmp_gt_r    |
| cmp_le_r      | cmp_lt_r      | cmp_ne_r    |             |

*   **Syntax:** `command_r min, max`
*   **Common Examples:**
    *   `pitchbend_r -20, 20` (Random detuning)
    *   `pan_r 0, 127` (Random panning position)
    *   `wait_r 40, 56` (Humanized timing)

#### D. Variables & Math
NITRO-Composer provides **16 Local Variables** (0-15) per sequence and **16 Global Variables** (16-31) shared across the system.

*   **`setvar varNo, value`**: Sets variable `varNo` to a specific `value`.
*   **`randvar varNo, max`**: Sets a variable to a random number between 0 and `max`.
*   **`addvar` / `subvar`**: Adds or subtracts a value from the current variable.
*   **`printvar varNo`**: Prints the variable's current value to the debug console (NITRO-Player only).

#### E. Logic & Conditions (`_if`)
You can make the sequence react to game states or random variables using a two-step process: **Compare** then **Execute**.

**1. Compare**
First, compare a variable against a value to set the internal "True/False" flag.
*   `cmp_eq varNo, value` (Checks if Equal)
*   `cmp_lt varNo, value` (Checks if Less Than)
*   `cmp_gt varNo, value` (Checks if Greater Than)

**2. Execute**
Append `_if` to **any** command. The command will only execute if the previous comparison was True.

> **Example: Probability (50% chance to play a note)**
> ```text
> randvar 0, 100         ; Roll dice (0-100) into Var 0
> cmp_lt 0, 50           ; Check: Is Var 0 < 50?
> cn4_if 127, 48         ; IF TRUE: Play Middle C
> ```
