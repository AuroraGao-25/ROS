#!/usr/bin/env python3
import json

import rospy
from std_msgs.msg import String


class ResponseManagerNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/attention/state")
        self.output_topic = rospy.get_param("~output_topic", "/audio/command")
        self.cooldown_seconds = rospy.get_param("~cooldown_seconds", 12.0)
        self.remind_after_seconds = rospy.get_param("~remind_after_seconds", 2.5)
        self.drowsy_wav_path = rospy.get_param("~drowsy_wav_path", "")

        self.messages = {
            "distracted": rospy.get_param("~distracted_text", "Please come back to focus."),
            "drowsy": rospy.get_param("~drowsy_text", "You look tired. Please take a short break."),
            "absent": rospy.get_param("~absent_text", "User is away."),
        }
        self.last_state = None
        self.state_since = None
        self.last_played_at = {}

        self.pub = rospy.Publisher(self.output_topic, String, queue_size=10)
        self.sub = rospy.Subscriber(self.input_topic, String, self.on_state, queue_size=10)
        rospy.loginfo("response_manager: %s -> %s", self.input_topic, self.output_topic)

    def on_state(self, msg):
        try:
            data = json.loads(msg.data)
        except ValueError:
            rospy.logwarn("response_manager received invalid JSON")
            return

        state = data.get("state", "unknown")
        now = float(data.get("stamp", rospy.Time.now().to_sec()))

        if state != self.last_state:
            self.last_state = state
            self.state_since = now

        if state not in self.messages:
            return

        stable_for = now - (self.state_since or now)
        if stable_for < self.remind_after_seconds:
            return

        last_played = self.last_played_at.get(state, 0.0)
        if now - last_played < self.cooldown_seconds:
            return

        command = {
            "stamp": now,
            "state": state,
            "action": "say",
            "text": self.messages[state],
            "priority": 1,
        }
        if state == "drowsy" and self.drowsy_wav_path:
            command["action"] = "play"
            command["wav_path"] = self.drowsy_wav_path

        self.last_played_at[state] = now
        self.pub.publish(json.dumps(command))
        rospy.loginfo("response_manager command: %s", command.get("wav_path", command["text"]))


if __name__ == "__main__":
    rospy.init_node("response_manager")
    ResponseManagerNode()
    rospy.spin()
