# AGENTS.md

## Project Overview

This repository contains **Focus Companion**, a ROS Python project for a Juno 2 based focus companion robot.

The robot observes a user through a camera and classifies the user into four attention states:

- `focused`
- `distracted`
- `drowsy`
- `absent`

The project intentionally avoids model training. It uses MediaPipe pre-trained face landmarks and simple rule-based logic, because the course grading focuses on ROS integration, node communication, and state-machine behavior.

## System Pipeline

The ROS data flow is:

```text
/camera/image_raw
  -> attention_detect
/attention/features
  -> attention_smoother
/attention/smoothed_features
  -> state_judge
/attention/state
  -> response_manager
/audio/command
  -> audio_player
```

The package is located at:

```text
focus_companion/
```

## ROS Nodes

### `attention_detect.py`

Subscribes to the camera image topic and uses MediaPipe Face Mesh to extract simple attention-related features.

Publishes:

```text
/attention/features
```

Main features:

- face detected or absent
- approximate head yaw
- approximate head pitch
- eye aspect ratio
- eye closed flag
- head turned flag
- head down flag

### `attention_smoother.py`

Maintains a short time-window buffer of raw features.

Publishes:

```text
/attention/smoothed_features
```

This follows the same high-level idea as the referenced emobot smoother: avoid judging from a single frame and instead use recent behavior over time.

### `state_judge.py`

Converts smoothed features into one of the project states:

```text
focused / distracted / drowsy / absent
```

Rules are deliberately simple and tunable through ROS parameters.

### `response_manager.py`

Maps attention states to robot responses.

Important behavior:

- Does not interrupt the user when state is `focused`.
- Waits until a non-focused state is stable for a short duration.
- Uses a cooldown to avoid repeated reminders.
- Sends a `play` command with `sounds/energize.wav` when the user is `drowsy`.

Publishes:

```text
/audio/command
```

### `audio_player.py`

Consumes audio commands and plays them with ROS `sound_play` when available.

If `sound_play` is unavailable, it falls back to console logging so the pipeline remains testable without robot audio hardware.

For `drowsy`, the default launch file points `response_manager/drowsy_wav_path` to:

```text
focus_companion/sounds/energize.wav
```

Replace that launch parameter to use another `.wav` file.

### `demo_state_driver.py`

Publishes scripted attention states without using a camera.

Use this node to verify the response and audio pipeline before testing MediaPipe camera detection.

## Launch Commands

Build inside a catkin workspace:

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

Run with a real camera:

```bash
roslaunch focus_companion focus_companion.launch camera_topic:=/camera/image_raw
```

Run without a camera:

```bash
roslaunch focus_companion focus_companion.launch use_demo_driver:=true
```

Inspect outputs:

```bash
rostopic echo /attention/state
rostopic echo /audio/command
```

## Dependencies

ROS dependencies:

- `rospy`
- `std_msgs`
- `sensor_msgs`
- `cv_bridge`
- `sound_play`

Python dependencies for camera detection:

```bash
pip install mediapipe opencv-python
```

On Juno 2, prefer using the robot's existing ROS and MediaPipe environment if available.

## Implementation Rules For Future Agents

When modifying this project:

- Keep the five-node architecture unless the user explicitly requests a redesign.
- Prefer ROS parameters for thresholds and timings.
- Do not add model training or external AI services.
- Keep message passing simple; the current implementation uses JSON inside `std_msgs/String` to avoid custom message compilation.
- Preserve the demo mode because it is useful for presentation and debugging.
- Keep audio behavior non-intrusive: no reminders during `focused`.
- Keep the drowsy music asset local or explicitly user-provided; do not introduce copyrighted audio.
- Avoid large unrelated refactors.
- Test at least Python syntax after code edits.

Recommended syntax check:

```bash
python -c "import ast, pathlib; files=list(pathlib.Path('focus_companion/scripts').glob('*.py')); [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in files]; print('syntax ok:', len(files), 'files')"
```

## Demo Story

Suggested final demo sequence:

```text
focused: user looks at screen
distracted: user looks away
drowsy: user lowers head or closes eyes
absent: user leaves camera view
```

The key demonstration goal is a stable ROS pipeline:

```text
camera -> features -> smoothing -> state -> response -> audio
```

The project should be presented as a ROS integration and state-management system, not as a machine-learning accuracy project.
