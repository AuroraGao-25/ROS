#!/usr/bin/env python3
import json

import rospy
from std_msgs.msg import String


class DemoStateDriver:
    def __init__(self):
        self.output_topic = rospy.get_param("~output_topic", "/attention/state")
        self.pub = rospy.Publisher(self.output_topic, String, queue_size=10)
        self.rate = rospy.Rate(2)
        self.timeline = [
            (20, "focused", "demo_focus"),
            (20, "distracted", "demo_look_away"),
            (20, "drowsy", "demo_sleepy"),
            (10, "absent", "demo_leave"),
            (20, "focused", "demo_return"),
        ]

    def run(self):
        rospy.loginfo("demo_state_driver publishing scripted states on %s", self.output_topic)
        start = rospy.Time.now().to_sec()
        while not rospy.is_shutdown():
            elapsed = (rospy.Time.now().to_sec() - start) % sum(item[0] for item in self.timeline)
            cursor = 0
            state = "focused"
            reason = "demo"
            for duration, candidate_state, candidate_reason in self.timeline:
                cursor += duration
                if elapsed <= cursor:
                    state = candidate_state
                    reason = candidate_reason
                    break
            self.pub.publish(json.dumps({
                "stamp": rospy.Time.now().to_sec(),
                "state": state,
                "reason": reason,
                "confidence": 1.0,
            }))
            self.rate.sleep()


if __name__ == "__main__":
    rospy.init_node("demo_state_driver")
    DemoStateDriver().run()
