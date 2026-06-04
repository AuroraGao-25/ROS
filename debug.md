# catkin_make
```
cd ~/catkin_ws
catkin_make
source devel/setup.bash
rospack find focus_companion  # /home/user/catkin_ws/src/focus_companion

chmod +x ~/catkin_ws/src/focus_companion/scripts/*.py

```


# 本地调试
```
ls /dev/video*  # our camera device path is: /dev/video2 

roslaunch focus_companion focus_companion_usb_cam.launch # run the code


```

# 本地视频调试
```
# 下载视频文件
cd ~/catkin_ws/src/focus_companion
mkdir -p test_videos

wget -O test_videos/head_pose_female.mp4 \
https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4

# 启动视频topic: 

rosrun focus_companion video_file_publisher.py \
  _video_path:=$HOME/catkin_ws/src/focus_companion/test_videos/focus_test.mp4 \
  _topic:=/sim_camera/image_raw \
  _fps:=15

# 确认视频流
rostopic hz /sim_camera/image_raw

# 启动主程序
roslaunch focus_companion focus_companion.launch \
  camera_topic:=/sim_camera/image_raw \
  show_debug_image:=false

# 看结果
rostopic echo /attention/features
rostopic echo /attention/state
rostopic echo /audio/command


# 固化到一个launch文件，再启动
roslaunch focus_companion focus_companion_video.launch
```

# 视频录制要求
正脸看屏幕 5 秒       → focused
转头看旁边 5 秒       → distracted
闭眼/低头 5 秒        → drowsy
离开画面 5 秒         → absent
回到画面 5 秒         → focused

# Monitor state
rosrun focus_companion monitor_state.py

# 根据monitor_state的返回值，重点调试state_judge的阈值
"face_visible_ratio"
"eye_closed_ratio"
"head_turned_ratio"
"head_down_ratio"
"avg_head_yaw"
"avg_head_pitch"
"avg_eye_aspect_ratio"

