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

Run with a real-time camera preview window:

```bash
roslaunch focus_companion focus_companion.launch camera_topic:=/camera/image_raw show_debug_image:=true
```

If your robot uses the `usb_cam` package, start both `usb_cam` and Focus Companion with:

```bash
roslaunch focus_companion focus_companion_usb_cam.launch
```

This launch subscribes Focus Companion to:

```text
/usb_cam/image_raw
```

If the preview window stays on "waiting for images", verify the camera topic:

```bash
rostopic list | grep image
rostopic info /camera/image_raw
rostopic hz /camera/image_raw
```

Replace `/camera/image_raw` with the real topic, such as `/camera/rgb/image_raw`.

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
pip install mediapipe
```

On a non-ROS laptop test environment, install `opencv-python` only if you want `show_debug_image:=true`. On the robot, `cv_bridge`, `sensor_msgs`, `std_msgs`, `rospy`, `sound_play`, and usually `cv2` should come from the ROS/Ubuntu environment.

## Jupiter ROS1 / Python 3.8.10 Notes

For the Jupiter ROS1 environment with Python `3.8.10`, use the pinned dependency file:

```bash
python3 -m pip install -r focus_companion/requirements-jupiter-py38.txt
```

Do not blindly install the latest MediaPipe on Python 3.8. Current MediaPipe releases no longer advertise Python 3.8 support, while `mediapipe==0.10.14` does.

Prefer the robot's existing ROS/OpenCV stack for `cv_bridge`. If `cv2` is already available through Ubuntu/ROS packages, avoid installing `opencv-python` with pip on the robot unless necessary.

Before running the launch file, make the scripts executable on the robot:

```bash
chmod +x focus_companion/scripts/*.py
```

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
