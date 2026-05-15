#!/usr/bin/env python3
import json

import rospy
from std_msgs.msg import String


class StateJudgeNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/attention/smoothed_features")
        self.output_topic = rospy.get_param("~output_topic", "/attention/state")

        self.absent_face_ratio = rospy.get_param("~absent_face_ratio", 0.25)
        self.drowsy_eye_ratio = rospy.get_param("~drowsy_eye_ratio", 0.55)
        self.drowsy_head_down_ratio = rospy.get_param("~drowsy_head_down_ratio", 0.65)
        self.distracted_head_turned_ratio = rospy.get_param("~distracted_head_turned_ratio", 0.55)
        self.min_samples = rospy.get_param("~min_samples", 5)

        self.pub = rospy.Publisher(self.output_topic, String, queue_size=10)
        self.sub = rospy.Subscriber(self.input_topic, String, self.on_smoothed_features, queue_size=10)
        rospy.loginfo("state_judge: %s -> %s", self.input_topic, self.output_topic)

    def judge(self, data):
        if data.get("sample_count", 0) < self.min_samples:
            return "unknown", "waiting_for_window"

        face_visible_ratio = float(data.get("face_visible_ratio", 0.0))
        eye_closed_ratio = float(data.get("eye_closed_ratio", 0.0))
        head_down_ratio = float(data.get("head_down_ratio", 0.0))
        head_turned_ratio = float(data.get("head_turned_ratio", 0.0))

        if face_visible_ratio < self.absent_face_ratio:
            return "absent", "face_not_visible"
        if eye_closed_ratio >= self.drowsy_eye_ratio or head_down_ratio >= self.drowsy_head_down_ratio:
            return "drowsy", "eyes_closed_or_head_down"
        if head_turned_ratio >= self.distracted_head_turned_ratio:
            return "distracted", "head_turned_away"
        return "focused", "face_forward_and_eyes_open"

    def on_smoothed_features(self, msg):
        try:
            data = json.loads(msg.data)
        except ValueError:
            rospy.logwarn("state_judge received invalid JSON")
            return

        state, reason = self.judge(data)
        output = {
            "stamp": data.get("stamp", rospy.Time.now().to_sec()),
            "state": state,
            "reason": reason,
            "confidence": self.confidence_for(state, data),
            "features": data,
        }
        self.pub.publish(json.dumps(output))
        rospy.loginfo_throttle(1.0, "attention state: %s (%s)", state, reason)

    @staticmethod
    def confidence_for(state, data):
        if state == "absent":
            return round(1.0 - float(data.get("face_visible_ratio", 0.0)), 3)
        if state == "drowsy":
            return round(max(float(data.get("eye_closed_ratio", 0.0)), float(data.get("head_down_ratio", 0.0))), 3)
        if state == "distracted":
            return round(float(data.get("head_turned_ratio", 0.0)), 3)
        if state == "focused":
            return round(float(data.get("face_visible_ratio", 0.0)) * (1.0 - float(data.get("head_turned_ratio", 0.0))), 3)
        return 0.0


if __name__ == "__main__":
    rospy.init_node("state_judge")
    StateJudgeNode()
    rospy.spin()
