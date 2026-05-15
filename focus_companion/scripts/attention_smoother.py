#!/usr/bin/env python3
import json
from collections import deque

import rospy
from std_msgs.msg import String


class AttentionSmootherNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/attention/features")
        self.output_topic = rospy.get_param("~output_topic", "/attention/smoothed_features")
        self.window_seconds = rospy.get_param("~window_seconds", 2.0)
        self.buffer = deque()

        self.pub = rospy.Publisher(self.output_topic, String, queue_size=10)
        self.sub = rospy.Subscriber(self.input_topic, String, self.on_features, queue_size=30)
        rospy.loginfo("attention_smoother: %s -> %s, %.1fs window", self.input_topic, self.output_topic, self.window_seconds)

    @staticmethod
    def ratio(items, key):
        if not items:
            return 0.0
        return sum(1 for item in items if item.get(key, False)) / float(len(items))

    @staticmethod
    def average(items, key):
        values = [float(item.get(key, 0.0)) for item in items]
        return sum(values) / float(len(values)) if values else 0.0

    def on_features(self, msg):
        try:
            features = json.loads(msg.data)
        except ValueError:
            rospy.logwarn("attention_smoother received invalid JSON")
            return

        now = float(features.get("stamp", rospy.Time.now().to_sec()))
        self.buffer.append(features)
        while self.buffer and now - float(self.buffer[0].get("stamp", now)) > self.window_seconds:
            self.buffer.popleft()

        items = list(self.buffer)
        smoothed = {
            "stamp": now,
            "window_seconds": self.window_seconds,
            "sample_count": len(items),
            "face_visible_ratio": self.ratio(items, "face_detected"),
            "eye_closed_ratio": self.ratio(items, "eye_closed"),
            "head_turned_ratio": self.ratio(items, "head_turned"),
            "head_down_ratio": self.ratio(items, "head_down"),
            "avg_head_yaw": round(self.average(items, "head_yaw"), 4),
            "avg_head_pitch": round(self.average(items, "head_pitch"), 4),
            "avg_eye_aspect_ratio": round(self.average(items, "eye_aspect_ratio"), 4),
            "latest": features,
        }
        self.pub.publish(json.dumps(smoothed))


if __name__ == "__main__":
    rospy.init_node("attention_smoother")
    AttentionSmootherNode()
    rospy.spin()
