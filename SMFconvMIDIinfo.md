Information on what MIDI features you can make use of with the SMFconv tool.

---
### 1. Note and Pitch
*   **Note On / Note Off:** Fully supported.
    *   Velocity is preserved.
    *   Note Off events are matched to Note On events
*   **Pitch Bend:** Supported.
*   **Program Change:** Supported.

### 2. Control Changes (CC) - Detailed Mapping
The tool maps standard MIDI CCs to specific sound engine commands.

| CC ID | Target Command | Description |
| :--- | :--- | :--- |
| **1** | `mod_depth` | Sets vibrato depth. |
| **5** | `porta_time` | Sets the speed/time for portamento. |
| **7** | `volume` | Channel volume. |
| **10** | `pan` | Stereo panning. |
| **11** | `volume2` | Expression (secondary volume). |
| **12** | `main_volume` | often Master Volume for the track. |
| **13** | `transpose` | Transposes the key (value - 64). |
| **14** | `prio` | Sets channel priority (for voice allocation). |
| **16-19**| `setvar 0-3` | Sets internal variables (logic/scripting). |
| **20** | `bendrange` | Sets pitch bend range semitones. |
| **21** | `mod_speed` | Vibrato speed. |
| **22** | `mod_type` | Vibrato waveform type. |
| **23** | `mod_range` | Vibrato range. |
| **26** | `mod_delay` | Delay before vibrato starts. |
| **28** | `sweep_pitch` | Pitch sweep (value - 64). |
| **65** | `porta_on/off` | Portamento switch (>=64 On, <64 Off). |
| **84** | `porta` | Portamento start point. |
| **85** | `attack` | Envelope Attack rate. |
| **86** | `decay` | Envelope Decay rate. |
| **87** | `sustain` | Envelope Sustain level. |
| **88** | `release` | Envelope Release rate. |
| **89** | `loop_start` | Sets a loop point. |
| **90** | `loop_end` | Jumps back to loop start. |

### 3. Meta Events & Structure
The tool relies heavily on Meta Events (FF xx ...) for logic and flow control.

*   **Tempo:** Supported.
*   **Time Signature (Meta 0x58):** parsed to validate measure alignment (`sub_40E300`), but does not appear to generate a specific runtime command. It is used to calculate measure boundaries for the text output comments (`"; Measure X"`).
*   **End of Track (Meta 0x2F):** Supported. Generates `fin` (finish) command.
*   **Track Name:** Read and used for file naming/labels.

### 4. Advanced Looping & Logic (Via Text Events)
This converter uses **Text Events (Meta 0x01)** to handle logic that standard MIDI doesn't support. It parses the text strings inside the MIDI file

*   **Loops:**
    *   If a text event contains `[` or `loop_sta`, it generates a `_LoopStart` label.
    *   If a text event contains `]` or `loop_end`, it generates a `jump _LoopStart` command.
*   **Raw Assembly Injection:**
    *   If a text event starts with `text_all`, the converter treats the rest of the text as raw assembly code to inject directly into the output file.
    *   It handles the token `$$` to possibly handle variable replacement or label generation.
*   **Wait:**
    *   While standard MIDI uses delta times, the text output explicitly generates `wait` commands based on the tick resolution.
