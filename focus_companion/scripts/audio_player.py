#!/usr/bin/env python3
import json

import rospy
from std_msgs.msg import String


class AudioPlayerNode:
    def __init__(self):
        self.input_topic = rospy.get_param("~input_topic", "/audio/command")
        self.voice = rospy.get_param("~voice", "voice_kal_diphone")
        self.volume = rospy.get_param("~volume", 1.0)
        self.sound_client = None

        try:
            from sound_play.libsoundplay import SoundClient
            self.sound_client = SoundClient()
            rospy.sleep(1.0)
            rospy.loginfo("audio_player using sound_play")
        except Exception as exc:
            rospy.logwarn("sound_play unavailable, falling back to console output: %s", exc)

        self.sub = rospy.Subscriber(self.input_topic, String, self.on_command, queue_size=10)
        rospy.loginfo("audio_player listening on %s", self.input_topic)

    def on_command(self, msg):
        try:
            command = json.loads(msg.data)
        except ValueError:
            rospy.logwarn("audio_player received invalid JSON")
            return

        action = command.get("action", "say")
        text = command.get("text", "")
        wav_path = command.get("wav_path")

        if self.sound_client and action == "play" and wav_path:
            try:
                self.sound_client.playWave(wav_path, volume=self.volume)
            except Exception as exc:
                rospy.logwarn("failed to play wave file %s: %s", wav_path, exc)
                if text:
                    self.sound_client.say(text, self.voice, volume=self.volume)
            return

        if self.sound_client and text:
            self.sound_client.say(text, self.voice, volume=self.volume)
            return

        rospy.loginfo("AUDIO: [%s] %s", command.get("state", "unknown"), text or wav_path or command)


if __name__ == "__main__":
    rospy.init_node("audio_player")
    AudioPlayerNode()
    rospy.spin()
