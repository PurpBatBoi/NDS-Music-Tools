This document outlines the available feature set SMFconv provides to convert Standard MIDI Files (SMF) for the Nintendo DS, and provides a complete reference for the supported commands.

---

# SMFconv Command Reference

### 1. DAW Text Event Syntax
To insert commands that do not have MIDI CC equivalents (like logic, looping, or setup), use **Meta Text Events** in your DAW.

| Prefix | Target | Example |
| :--- | :--- | :--- |
| **`text_all:`** | All Tracks | `text_all: notewait_off` (Enable Chords globally) |
| **`text_XX:`** | Specific Track | `text_00: call pattern_a` (Target Track 0/MIDI Ch 1) |
| **`[`** / **`]`** | Loop Markers | Insert `[` to start a global loop, `]` to end it. |

---

### 2. Standard MIDI Messages
Natively supported events with specific engine behaviors.

*   **Note On / Note Off**
    *   **Velocity:** Supported (0–127). Uses **squared value scaling** ($velocity^2$). 127 is 100% volume; 64 is approx 25% volume.
    *   **Key Mapping:** Middle C (MIDI Note 60) = `cn4`.
    *   *Example:* `cn4 127, 48` (Play Middle C at max volume for 1 quarter note).
*   **Pitch Bend**
    *   Fully supported via the Pitch Wheel. Range set by `bendrange`.
*   **Program Change**
    *   Maps to the `prg` command to change instruments.
    *   *Example:* `prg 14` (Switch to instrument 14).

---

### 3. Playback & Structure
These commands control track organization and timing. They generally must be entered as Text Events.

| Command | Arguments | Description | MIDI CC |
| :--- | :--- | :--- | :--- |
| **`tempo`** | `[0-1023]` | Sets BPM (Default: 120). | — |
| **`prg`** | `[0-127]` | Changes instrument/program. | **PC** |
| **`fin`** | — | **Required.** Marks end of track. | — |
| **`wait`** | `[length]` | Pauses cursor for duration (48 ticks = Quarter note). | — |
| **`alloctrack`** | `[mask]` | Allocates memory for tracks (Must be first command). | — |
| **`opentrack`** | `[no], [label]`| Starts a parallel track number at a specific label. | — |
| **`notewait_off`**| — | Enables **Polyphony** (play without stopping cursor). | — |
| **`prio`** | `[0-127]` | Sets voice priority (Higher wins voice allocation). | **CC 14** |

**Structure Example:**
```text
alloctrack 0x00ff      ; Allocate memory for the track (0x00ff = 255)
opentrack 1, MyTrack1  ; Start Track 1 at the "MyTrack1" label
notewait_off           ; Track 0 can now play chords
cn4 127, 48            ; Note 1 of chord
en4 127, 48            ; Note 2 of chord
gn4 127, 48            ; Note 3 of chord
fin
```

#### Note Lenghts:

| Note Type | Math | **Tick Value** |
| :--- | :--- | :--- |
| **Whole Note** | $48 \times 4$ | **192** |
| **Half Note** | $48 \times 2$ | **96** |
| **Quarter Note** | Base | **48** |
| **8th Note** | $48 / 2$ | **24** |
| **16th Note** | $48 / 4$ | **12** |
| **32nd Note** | $48 / 8$ | **6** |
| **64th Note** | $48 / 16$ | **3** |

#### Dotted Note Lengths (Base value + 50%)
| Note Type | Math | **Tick Value** |
| :--- | :--- | :--- |
| **Dotted Half** | $96 \times 1.5$ | **144** |
| **Dotted Quarter** | $48 \times 1.5$ | **72** |
| **Dotted 8th** | $24 \times 1.5$ | **36** |
| **Dotted 16th** | $12 \times 1.5$ | **18** |
| **Dotted 32nd** | $6 \times 1.5$ | **9** |

#### Triplet Note Lengths (1/3 of a parent value)
| Note Type | Math | **Tick Value** |
| :--- | :--- | :--- |
| **Quarter Triplet** | $96 / 3$ | **32** |
| **8th Triplet** | $48 / 3$ | **16** |
| **16th Triplet** | $24 / 3$ | **8** |
| **32nd Triplet** | $12 / 3$ | **4** |

---

### 4. Sound Shaping (Envelope & Mix)
Controls volume, stereo placement, and ADSR envelopes.

| Command | Arguments | Description | MIDI CC |
| :--- | :--- | :--- | :--- |
| **`volume`** | `[0-127]` | Track Volume (Uses squared scaling). | **CC 07** |
| **`volume2`** | `[0-127]` | Expression/Secondary Volume. | **CC 11** |
| **`main_volume`**| `[0-127]` | Master Volume for the whole player. | **CC 12** |
| **`pan`** | `[0-127]` | 0=Left, 64=Center, 127=Right. | **CC 10** |
| **`attack`** | `[0-127]` | Envelope Attack Rate (Overrides SBNK setting). | **CC 85** |
| **`decay`** | `[0-127]` | Envelope Decay Rate (Overrides SBNK setting). | **CC 86** |
| **`sustain`** | `[0-127]` | Envelope Sustain Level (Overrides SBNK setting). | **CC 87** |
| **`release`** | `[0-127]` | Envelope Release Rate (Overrides SBNK setting). | **CC 88** |

**Example (L/R Pan):**
```text
pan 0       ; Hard Left
wait 48     ; Wait 1 beat
pan 64      ; Center
wait 48     ; Wait 1 beat
pan 127     ; Hard Right
```

---

### 5. Pitch & Portamento
Controls tuning, sliding, and sweep effects.

| Command | Arguments | Description | MIDI CC |
| :--- | :--- | :--- | :--- |
| **`pitchbend`** | `[-128 to 127]` | Bends pitch up or down. | **Wheel** |
| **`bendrange`** | `[0-127]` | Bend range in semitones (Def: 2). | **CC 20** |
| **`transpose`** | `[-64 to 63]` | Transposes key in semitones. | **CC 13*** |
| **`porta_on/off`**| — | Enables/Disables note sliding (Legato). | **CC 65** |
| **`porta_time`** | `[0-255]` | Speed of the slide (0=Fast, 255=Slow). | **CC 05** |
| **`porta`** | `[key]` | Sets the start note for the slide. | **CC 84** |
| **`sweep_pitch`** | `[-64 to 63]` | Hardware pitch sweep effect. | **CC 28** |

*\*Note: For CC13 (Transpose), Value 64 is center (0 semitones).*

**Example (Legato Slide):**
```text
porta_on        ; Enable sliding
porta_time 40   ; Set slide speed
cn4 127, 48     ; Start at C
wait 48
gn4 127, 48     ; Slide up to G
```

---

### 6. Modulation (LFO)
Automates movement. You can modulate Pitch (Vibrato), Volume (Tremolo), or Pan (Auto-pan).

| Command | Arguments | Description | MIDI CC |
| :--- | :--- | :--- | :--- |
| **`mod_depth`** | `[0-127]` | Intensity of effect. | **CC 01** |
| **`mod_speed`** | `[0-127]` | Speed of LFO oscillation. | **CC 21** |
| **`mod_type`** | `[0-2]` | 0=Pitch, 1=Volume, 2=Pan. | **CC 22** |
| **`mod_range`** | `[0-127]` | Multiplier for the depth. | **CC 23** |
| **`mod_delay`** | `[0-127]` | Delay before LFO starts (~5ms units). | **CC 26** |

**Example (Auto-Pan setup):**
```text
mod_type 2      ; Set LFO to Panning
mod_speed 30    ; Medium speed
mod_depth 127   ; Full Left-to-Right swing
```

---

### 7. Flow Control & Logic
Used to create loops, branching, subroutines, and logic. These commands **must** be entered as Text Events.

#### Branching
*   **`jump [label]`**: Unconditional jump. Used for infinite loops.
*   **`call [label]`**: Jumps to a "subroutine" (pattern).
*   **`ret`**: Returns from a subroutine.
*   **`loop_start [count]`**: Starts a loop block. (CC 89).
*   **`loop_end`**: Ends a loop block. (CC 90).

**Subroutine Example:**
```text
Main:
    call MyDrumPattern   ; Play pattern once
    call MyDrumPattern   ; Play pattern again
    jump Main            ; Loop the whole song

MyDrumPattern:           ; The reusable pattern
    cn3 127, 12
    wait 12
    cn3 127, 12
    wait 36
    ret                  ; Go back to where "call" was
```

---

### 8. Variables & Math
There are **16 Local Variables** (0-15) and **16 Global Variables** (16-31). Global variables allow communication between the music and the game code.

| Command | Description | MIDI CC |
| :--- | :--- | :--- |
| **`setvar [0-3], [val]`** | Sets local variables 0 through 3. | **CC 16-19** |
| **`setvar [var], [val]`** | Sets any variable (Text Event only). | — |
| **`randvar [var], [max]`**| Sets variable to random number 0-Max. | — |
| **`addvar` / `subvar`** | Adds or subtracts values. | — |
| **`mulvar` / `divvar`** | Multiplies or divides values. | — |

#### Conditional Execution
To use logic, compare a variable against a value to set a flag, then append `_if` to the next command.

*   **`cmp_eq [var], [val]`**: Checks if Equal.
*   **`cmp_lt` / `cmp_gt`**: Checks if Less Than / Greater Than.
*   **`cmp_le` / `cmp_ge`**: Checks if Less/Equal / Greater/Equal.


**Example (Random Logic):**
```text
randvar 0, 1      ; Variable 0 becomes 0 or 1
cmp_eq 0, 1       ; Check: Is Var 0 == 1?
jump_if RarePath  ; If yes, jump to RarePath label

; -- Regular Path --
cn4 127, 48
fin

RarePath:
cn5 127, 48
fin
```

---

### 9. Command Suffixes
You can extend almost any standard command by adding these suffixes in the Text Event editor.

*   **`_r` (Random):** Picks a value between min and max.
    *   *Ex:* `volume_r 80, 127` (Humanizes volume).

   * **Table of supported randomized commands:**

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

*   **`_v` (Variable):** Uses a variable's value instead of a static number.
    *   *Ex:* `pan_v 0` (Sets pan to value of Var 0).
*   **`_if` (Conditional):** Executes only if the last comparison was True.
    *   *Ex:* `jump_if loop_start` (Loops only if the check was True).
