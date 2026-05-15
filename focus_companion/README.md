# Focus Companion

ROS Python demo for a Juno 2 focus companion robot. The robot estimates four attention states:

- `focused`
- `distracted`
- `drowsy`
- `absent`

The design intentionally uses simple MediaPipe features plus ROS node communication, because the course project focuses on ROS integration instead of AI model training.

## Nodes

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

## Quick Run On ROS

Put this folder inside a catkin workspace `src` directory, then build:

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

Run with a real camera topic:

```bash
roslaunch focus_companion focus_companion.launch camera_topic:=/camera/image_raw
```

Run without a camera, using a scripted demo state sequence:

```bash
roslaunch focus_companion focus_companion.launch use_demo_driver:=true
```

Watch the state output:

```bash
rostopic echo /attention/state
```

Watch audio commands:

```bash
rostopic echo /audio/command
```

## Python Dependencies

The real camera node needs:

```bash
pip install mediapipe opencv-python
```

On Juno 2, `cv_bridge`, `sensor_msgs`, `std_msgs`, `rospy`, and `sound_play` should come from the ROS environment.

## Tuning Parameters

Useful launch/node parameters:

- `attention_smoother/window_seconds`: default `2.0`
- `state_judge/absent_face_ratio`: default `0.25`
- `state_judge/drowsy_eye_ratio`: default `0.55`
- `state_judge/drowsy_head_down_ratio`: default `0.65`
- `state_judge/distracted_head_turned_ratio`: default `0.55`
- `response_manager/remind_after_seconds`: default `2.5`
- `response_manager/cooldown_seconds`: default `12.0`
- `response_manager/drowsy_wav_path`: default from launch is `$(find focus_companion)/sounds/energize.wav`

When the state is `drowsy`, `response_manager` sends a `play` command so `audio_player` plays a short energizing WAV file. To use your own music, replace `drowsy_wav_path` with another `.wav` path.

For the final demo, start with the scripted driver first. Once the audio behavior is correct, switch to the camera pipeline and tune thresholds in small steps.
