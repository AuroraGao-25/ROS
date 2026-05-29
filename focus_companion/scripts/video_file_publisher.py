#!/usr/bin/env python3
import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


def main():
    rospy.init_node("video_file_publisher")

    video_path = rospy.get_param("~video_path", "")
    topic = rospy.get_param("~topic", "/sim_camera/image_raw")
    fps = rospy.get_param("~fps", 15.0)
    loop = rospy.get_param("~loop", True)

    if not video_path:
        rospy.logerr("Missing parameter: _video_path:=/path/to/video.mp4")
        return

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        rospy.logerr("Cannot open video file: %s", video_path)
        return

    bridge = CvBridge()
    pub = rospy.Publisher(topic, Image, queue_size=1)

    rate = rospy.Rate(fps)

    rospy.loginfo("Publishing video file:")
    rospy.loginfo("  video_path: %s", video_path)
    rospy.loginfo("  topic:      %s", topic)
    rospy.loginfo("  fps:        %s", fps)

    while not rospy.is_shutdown():
        ok, frame = cap.read()

        if not ok:
            if loop:
                rospy.loginfo("Video ended. Looping from beginning.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                rospy.loginfo("Video ended. Exiting.")
                break

        msg = bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = "sim_camera"

        pub.publish(msg)
        rate.sleep()

    cap.release()


if __name__ == "__main__":
    main()