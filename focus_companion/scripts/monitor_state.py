#!/usr/bin/env python3
import json
import rospy
from std_msgs.msg import String


def callback(msg):
    try:
        data = json.loads(msg.data)
    except Exception as e:
        rospy.logwarn("Failed to parse state JSON: %s", e)
        return

    state = data.get("state", "unknown")
    reason = data.get("reason", "")
    confidence = data.get("confidence", 0.0)
    features = data.get("features", {})

    print("=" * 60)
    print("STATE:      {}".format(state))
    print("REASON:     {}".format(reason))
    print("CONFIDENCE: {:.2f}".format(confidence))
    print("face_visible_ratio:   {}".format(features.get("face_visible_ratio")))
    print("eye_closed_ratio:     {}".format(features.get("eye_closed_ratio")))
    print("head_turned_ratio:    {}".format(features.get("head_turned_ratio")))
    print("head_down_ratio:      {}".format(features.get("head_down_ratio")))
    print("avg_head_yaw:         {}".format(features.get("avg_head_yaw")))
    print("avg_head_pitch:       {}".format(features.get("avg_head_pitch")))
    print("avg_eye_aspect_ratio: {}".format(features.get("avg_eye_aspect_ratio")))


def main():
    rospy.init_node("monitor_state")
    rospy.Subscriber("/attention/state", String, callback)
    rospy.spin()


if __name__ == "__main__":
    main()