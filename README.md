# Bladework

3D figure skating program builder. Enter a program element by element (ISU codes with the moment of takeoff), drop in the music, and watch a 3D skater perform it on a regulation rink: jumps up to quads, spins by position, step and choreographic sequences, connecting skating built on edges and crossovers, and a first pass at pairs (twists, throws, lifts, death spirals, pair spins).

Includes short and free program rule checks for singles and pairs (ISU 2026/27), base values, tempo detection with beat snapping, slow-motion jump replays, five cameras and video export.

Live site: https://notjut.github.io/goldstudio/

## Motion capture

Jump animation is driven by motion-capture recordings converted from the FS-Jump3D dataset (Tanaka, Suzuki & Fujii, MMSports '24; CC BY-NC-SA 4.0), used here for development and research only. The converter (`convert.py` in the project notes) levels each recording to the ice plane, detects flight from the free-fall of the centre of mass, counts in-air rotations and retargets joint directions to the skater rig.
