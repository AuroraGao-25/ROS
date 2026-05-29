#!/usr/bin/env python3
import json
import math

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String


class AttentionDetectNode:
    def __init__(self):
        self.camera_topic = rospy.get_param("~camera_topic", "/camera/image_raw")
        self.output_topic = rospy.get_param("~output_topic", "/attention/features")
        self.show_debug_image = rospy.get_param("~show_debug_image", False)
        self.max_no_face_pitch = rospy.get_param("~max_no_face_pitch", 99.0)
        self.eye_closed_ear = rospy.get_param("~eye_closed_ear", 0.19)
        self.head_yaw_threshold = rospy.get_param("~head_yaw_threshold", 0.23)
        self.head_down_pitch_threshold = rospy.get_param("~head_down_pitch_threshold", 0.18)
        self.debug_window_name = "focus_companion attention_detect"
        self.latest_debug_frame = None
        self.last_image_time = None

        try:
            import mediapipe as mp
            from cv_bridge import CvBridge
        except Exception as exc:
            rospy.logerr("attention_detect requires cv_bridge and mediapipe: %s", exc)
            raise

        self.cv2 = None
        self.np = None
        if self.show_debug_image:
            try:
                import cv2
                import numpy as np
                self.cv2 = cv2
                self.np = np
                self.cv2.namedWindow(self.debug_window_name, self.cv2.WINDOW_NORMAL)
            except Exception as exc:
                rospy.logwarn("OpenCV cv2 is unavailable, disabling debug image: %s", exc)
                self.show_debug_image = False

        self.mp = mp
        self.bridge = CvBridge()
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.pub = rospy.Publisher(self.output_topic, String, queue_size=10)
        self.sub = rospy.Subscriber(self.camera_topic, Image, self.on_image, queue_size=1, buff_size=2**24)
        if self.show_debug_image:
            self.debug_timer = rospy.Timer(rospy.Duration(0.2), self.on_debug_timer)
        rospy.loginfo("attention_detect: %s -> %s", self.camera_topic, self.output_topic)

    @staticmethod
    def dist(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def eye_aspect_ratio(self, landmarks, side):
        if side == "left":
            ids = [33, 160, 158, 133, 153, 144]
        else:
            ids = [362, 385, 387, 263, 373, 380]
        p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in ids]
        horizontal = self.dist(p1, p4)
        if horizontal <= 1e-6:
            return 0.0
        return (self.dist(p2, p6) + self.dist(p3, p5)) / (2.0 * horizontal)

    def estimate_features(self, landmarks):
        nose = landmarks[1]
        chin = landmarks[152]
        left_eye_outer = landmarks[33]
        right_eye_outer = landmarks[263]
        forehead = landmarks[10]

        face_center_x = (left_eye_outer.x + right_eye_outer.x) / 2.0
        eye_width = abs(right_eye_outer.x - left_eye_outer.x)
        yaw = 0.0 if eye_width <= 1e-6 else (nose.x - face_center_x) / eye_width

        face_height = abs(chin.y - forehead.y)
        face_center_y = (forehead.y + chin.y) / 2.0
        pitch = 0.0 if face_height <= 1e-6 else (nose.y - face_center_y) / face_height

        left_ear = self.eye_aspect_ratio(landmarks, "left")
        right_ear = self.eye_aspect_ratio(landmarks, "right")
        ear = (left_ear + right_ear) / 2.0

        return {
            "face_detected": True,
            "head_yaw": round(yaw, 4),
            "head_pitch": round(pitch, 4),
            "eye_aspect_ratio": round(ear, 4),
            "eye_closed": ear < self.eye_closed_ear,
            "head_turned": abs(yaw) > self.head_yaw_threshold,
            "head_down": pitch > self.head_down_pitch_threshold,
            "quality": 1.0,
        }

    def on_image(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            rospy.logwarn_throttle(2.0, "cv_bridge conversion failed: %s", exc)
            return

        rgb = frame[:, :, ::-1].copy()
        result = self.face_mesh.process(rgb)

        if result.multi_face_landmarks:
            landmarks = result.multi_face_landmarks[0].landmark
            features = self.estimate_features(landmarks)
            if self.show_debug_image:
                self.mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    result.multi_face_landmarks[0],
                    self.mp.solutions.face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp.solutions.drawing_styles.get_default_face_mesh_contours_style(),
                )
        else:
            features = {
                "face_detected": False,
                "head_yaw": 0.0,
                "head_pitch": self.max_no_face_pitch,
                "eye_aspect_ratio": 0.0,
                "eye_closed": False,
                "head_turned": False,
                "head_down": False,
                "quality": 0.0,
            }

        features["stamp"] = msg.header.stamp.to_sec() if msg.header.stamp else rospy.Time.now().to_sec()
        self.pub.publish(json.dumps(features))

        if self.show_debug_image:
            self.draw_debug_overlay(frame, features)
            self.latest_debug_frame = frame
            self.last_image_time = rospy.Time.now()
            rospy.loginfo_throttle(3.0, "attention_detect receiving images from %s", self.camera_topic)

    def on_debug_timer(self, _event):
        if not self.show_debug_image:
            return

        if self.latest_debug_frame is None:
            frame = self.np.zeros((360, 640, 3), dtype=self.np.uint8)
            lines = [
                "Focus Companion Camera View",
                "waiting for images...",
                "topic: {}".format(self.camera_topic),
                "check: rostopic hz {}".format(self.camera_topic),
            ]
            for idx, text in enumerate(lines):
                y = 40 + idx * 34
                self.cv2.putText(frame, text, (20, y), self.cv2.FONT_HERSHEY_SIMPLEX, 0.72, (80, 255, 80), 2, self.cv2.LINE_AA)
        else:
            frame = self.latest_debug_frame

        try:
            self.cv2.imshow(self.debug_window_name, frame)
            self.cv2.waitKey(1)
        except Exception as exc:
            rospy.logwarn_throttle(5.0, "debug image window failed: %s", exc)

    def draw_debug_overlay(self, frame, features):
        status = "face" if features["face_detected"] else "no face"
        lines = [
            "Focus Companion Camera View",
            "status: {}".format(status),
            "yaw: {:.3f}  pitch: {:.3f}".format(features["head_yaw"], features["head_pitch"]),
            "ear: {:.3f}".format(features["eye_aspect_ratio"]),
            "eye_closed: {}  head_turned: {}  head_down: {}".format(
                features["eye_closed"],
                features["head_turned"],
                features["head_down"],
            ),
        ]
        for idx, text in enumerate(lines):
            y = 28 + idx * 24
            self.cv2.putText(frame, text, (12, y), self.cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 4, self.cv2.LINE_AA)
            self.cv2.putText(frame, text, (12, y), self.cv2.FONT_HERSHEY_SIMPLEX, 0.58, (80, 255, 80), 1, self.cv2.LINE_AA)


if __name__ == "__main__":
    rospy.init_node("attention_detect")
    AttentionDetectNode()
    rospy.spin()
