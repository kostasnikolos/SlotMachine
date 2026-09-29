# Audio Architecture Plan for Slot Engine

## 1. Web Audio & Tone.js Setup and Asset Loading Pipeline

The slot engine will utilize the standard Web Audio API, potentially augmented by Tone.js if advanced scheduling is required. However, the core pipeline involves:
- **Preloading Assets:** A central `AudioController` class (in JavaScript/TypeScript) will load all necessary `.wav` files during the initial boot sequence of the game.
- **Decoding & Buffering:** Fetched `.wav` files will be decoded into `AudioBuffer` objects.
- **Playback Architecture:** The `AudioController` will expose methods to trigger these buffers (e.g., `playReelStop()`, `playSpinLoop()`). Playback will use `AudioBufferSourceNode` routed through a global `GainNode` (for master volume control) before reaching the `AudioContext.destination`.
- **Concurrency:** The system must support overlapping sounds, especially for reel stops and background ambience.

## 2. Sound Effect Requirements (Creative Direction)

Based on the requested creative direction, the audio profile is defined as follows:

*   **"Spanking" (Reel Hit/Stop):** A sharp, heavy slap or impact sound. This will be triggered each time a reel slams into its final position. It requires a fast attack, a dense noise/transient body, and a quick decay.
*   **"Chain Deep Diving" (Spin/Tension):** Metallic dragging and clanking. This will be the looping sound of the reels spinning, evoking a heavy chain being pulled into the deep sea. It needs to sound metallic, heavy, and rhythmic.
*   **"Breathing on an Oxygen Mask" (Ambient Idle State):** Rhythmic, muffled, deep-sea breathing. This plays continuously in the background to build atmosphere while the player is idle or making decisions. It requires a slow, sweeping filter over a noise source to simulate inhaling and exhaling.

## 3. Technical Implementation Strategy: Procedural Audio Synthesis

We currently lack a pre-existing sound library. Instead of relying on external assets or synthesizing everything in real-time in the browser (which can be CPU-intensive and inconsistent across browsers), we will generate our audio assets offline using **Python**.

*   **Synthesis Method:** We will write Python scripts utilizing the standard `wave` and `math` (or `struct`) modules to mathematically generate the audio data.
*   **Output:** These scripts will output standard 16-bit, 44.1kHz `.wav` files.
*   **Integration:** The generated `.wav` files will be placed in the game's static assets directory and loaded by the Web Audio API pipeline described in Section 1. This guarantees consistent playback across all clients while keeping the game payload small.

## 4. Audio Builder Roadmap (3 Milestones)

To execute this plan, the Audio Builder agent will follow this 3-milestone roadmap:

### Milestone 1: Core Synthesis Scripts
*   Write Python scripts to generate the three core sounds:
    *   `generate_spank.py` (Reel stop)
    *   `generate_chain.py` (Spinning loop)
    *   `generate_breath.py` (Idle ambience)
*   Ensure scripts run cleanly without external dependencies (beyond standard Python library modules like `wave`, `math`, `struct`, `random`).
*   Output the corresponding `.wav` files into a designated `assets/audio/` directory.

### Milestone 2: Web Audio Controller Implementation
*   Develop the JavaScript/TypeScript `AudioController` module.
*   Implement the asynchronous loading and decoding pipeline for the generated `.wav` files.
*   Implement master volume control and basic playback methods (play once, play loop, stop).

### Milestone 3: Game Engine Integration
*   Integrate the `AudioController` into the main slot engine game loop.
*   Trigger the "Breathing" ambience on game start.
*   Trigger the "Chain" loop when a spin begins, and stop it when all reels stop.
*   Trigger the "Spanking" impact precisely when each individual reel lands on its final result.
