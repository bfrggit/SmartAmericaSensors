import socket
import string
import random
import time
import iwlib
from time import sleep
#import mosquitto
#from mosquitto import Mosquitto
import paho.mqtt.client
from paho.mqtt.client import Client as Paho


import logging
log = logging.getLogger(__name__)

from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

class MQTTSpeedTest(ThreadedVirtualSensor):
	def __init__(self, broker, device,
			topic="test",
			hostname=None,
			hostport=1883,
			username=None,
			password=None,
			keepalive=10,
			chunk_size=4096,
			chunk_repeat=16,
			query_in_failure=4,
			wait_max_failure=20.0,
			if_name=None, #XXX
			debug=False):
		super(MQTTSpeedTest, self).__init__(broker, device=device, interval=0, process=False, n_threads=1)

		if type(chunk_size) != type(9) or type(chunk_repeat) != type(9):
			raise TypeError
		if chunk_size < 0 or chunk_repeat < 1:
			raise ValueError

		self._client = Paho()
		self._client.on_connect = self._on_connect
		self._client.on_disconnect = self._on_disconnect
		self._client.on_publish = self._on_publish

		self._hostname = hostname
		self._hostport = hostport
		#self._username = username
		#self._password = password
		self._keepalive = keepalive
		self._topic = topic

		if username is not None and password is not None:
			self._client.username_pw_set(username, password)

		self._c_size = chunk_size
		self._c_repeat = chunk_repeat
		self._q_fail = query_in_failure
		self._w_fail = wait_max_failure

		#XXX: This interface name is only used by _get_essid
		"""
		It has no control on which interface to use by test traffic.
		This should be solved later,
			by allowing _get_essid to recognize correct netowrk if possible
		"""
		self._if_name = if_name

		self._run_flag = None
		self._neta = None
		self._lasttime = None
		self._debug = debug
	
	DEFAULT_PRIORITY = 7

	def _on_connect(self, mosq, obj, rc):
		pass

	def _on_disconnect(self, mosq, obj, rc):
		pass

	def _on_publish(self, mosq, obj, mid):
		mosq.disconnect()

	def _try_connect(self):
		try:
			self._client.connect(self._hostname, self._hostport, self._keepalive)
		except (socket.gaierror, socket.error):
			return False
		return True

	def check_available(self, event):
		if self._neta is not None and not self._neta:
			return False
		return True

	def on_event(self, event, topic):
		et = event.get_type()
		ed = event.get_raw_data()

		if et == "internet_access":
			self._neta = ed
		if et == "cmd_mqtt_speed_test":
			if ed:
				if self._run_flag is None:
					self._start()
				else:
					# Test is already running
					if self._debug:
						self.publish(self._debug_make_event("debug_mqtt_speed_test_cmd_failure", True, priority=7))
			else:
				if self._run_flag:
					self._stop()
				else:
					if self._debug:
						self.publish(self._debug_make_event("debug_mqtt_speed_test_cmd_failure", False, priority=7))

	def get_type(self):
		return "mqtt_speed"
	
	S = string.digits + string.lowercase + string.uppercase + string.punctuation
	
	def read_raw(self):
		if not self.check_available(None):
			log.info("no Internet access")
			sleep(self._q_fail)
			return None

		# Test network speed and return
		ts = 0.0
		td = 0.0
		count = 0
		for j in xrange(0, self._c_repeat):
			tb = time.time()
			if not self._try_connect():
				log.warning("connection failure")
				sleep(self._q_fail)
				break
			td += time.time() - tb
			message = "".join([random.choice(self.S) for _ in range(self._c_size)])
			tb = time.time()
			self._client.publish(self._topic, message, 0)
			self._client.loop_forever()
			ts += time.time() - tb
			count += 1
		speed = 0.0
		if count <= 0:
			return None
		try:
			speed = self._c_size * count / ts
			self._lasttime = time.time()
		except ZeroDivisionError:
			if self._c_size * count == 0: # Should not happen
				speed = float("nan")
			else: # Should not happen either
				speed = float("inf")
		delay = td / count
		essid = self._get_essid()

		res = {}
		res["speed"] = speed
		res["delay"] = delay # MQTT connection overhead
		if essid is not None:
			res["essid"] = essid

		if self._debug:
			self.publish(self._debug_make_event("debug_mqtt_speed_test_result", (speed, delay), priority=9))
		return res
	
	def policy_check(self, event):
		raw = event.get_raw_data()
		if type(raw) != type(dict()) or "speed" not in raw or raw["speed"] != raw["speed"]:
			if self._lasttime + self._w_fail < time.time():
				self._stop()
			return False
		return True

	def _start(self):
		# This method is called manually to trigger sensor loop
		self.run_in_background(self.sensor_loop, self._wait_period)
	
	def _stop(self):
		# This method is called either manually or automatically to allow sensor loop to stop
		self._run_flag = False

	def on_start(self):
		# Will not trigger sensor loop when "started" by client core
		pass

	def sensor_loop(self, interval):
		self._run_flag = True
		if self._debug:
			self.publish(self._debug_make_event("debug_mqtt_speed_test_run", True, priority=9))
		self._lasttime = time.time()
		while self._run_flag:
			self._do_sensor_read()
			sleep(interval)
		self._lasttime = None
		if self._debug:
			self.publish(self._debug_make_event("debug_mqtt_speed_test_run", False, priority=9))
		self._run_flag = None

	def _debug_make_event(self, event_type, value, priority=None):
		event = self.make_event_with_raw_data(value)
		event.data["event"] = event_type
		if type(priority) == type(9):
			event.priority = priority
		log.debug("debug event type: " + event_type)
		return event

	def _get_essid(self):
		#XXX: This does not gurantee correct ESSID if device has more than one available networks
		# Improvement needed

		if type(self._if_name) != type(""):
			return None

		iwconf = iwlib.get_iwconfig(self._if_name)
		if type(iwconf) != type(dict()) or "ESSID" not in iwconf:
			return None
		return iwconf["ESSID"]

