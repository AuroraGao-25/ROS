cmake_minimum_required(VERSION 3.0.2)
project(focus_companion)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  cv_bridge
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/attention_detect.py
  scripts/attention_smoother.py
  scripts/state_judge.py
  scripts/response_manager.py
  scripts/audio_player.py
  scripts/demo_state_driver.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(DIRECTORY sounds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
