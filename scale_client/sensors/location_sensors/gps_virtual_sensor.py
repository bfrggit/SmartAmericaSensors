from scale_client.sensors.virtual_sensor import VirtualSensor
from gps_poller import GPSPoller

import json
import time
import logging
log = logging.getLogger(__name__)

class GPSVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=1, exp=10, debug=False, debug_interval=10):
		super(GPSVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._exp = exp
		self._gps_poller = None
		self._debug_flag = debug
		self._debug_interval = debug_interval
		self._last_mode = None
		self._last_location = None
		self._mode_timer = None
		self._location_timer = None

	DEFAULT_PRIORITY = 7

	def on_start(self):
		self._gps_poller = GPSPoller()
		self._gps_poller.daemon = True
		self._gps_poller.start()
		super(GPSVirtualSensor, self).on_start()

	def get_type(self):
		return "gps"

	def read_raw(self):
		if self._gps_poller is None:
			return None
		raw = self._gps_poller.get_dict()
		if type(raw) != type({}):
			return None
		if self._debug_flag:
			self._debug(raw)
		raw["exp"] = time.time() + self._exp
		return raw
	
	def read(self):
		raw = self.read_raw()
		event = self.make_event_with_raw_data(raw, priority=7)
		return event

	def policy_check(self, data):
		raw = data.get_raw_data()
		if raw is None or type(raw) != type({}):
			return False
		if not "mode" in raw or raw["mode"] < 2:
			return False
		if not "lat" in raw or not "lon" in raw:
			return False
		return True

	def _debug(self, raw):
		from geopy import distance

		if not "mode" in raw: # Should not happen
			log.warning("invalid reading from GPS poller without GPS mode")
			return
		if not "lat" in raw or not "lon" in raw: # Should not happen
			log.warning("invalid reading from GPS poller without GPS location")
			return

		# Events for mode changes
		this_mode = raw["mode"]
		if this_mode != self._last_mode: # GPS mode changed
			self.publish(self._debug_make_event("debug_gps_mode", this_mode))
			self._mode_timer = time.time()
		elif self._mode_timer is None:
			self._mode_timer = time.time()
		elif self._mode_timer + self._debug_interval < time.time():
			self.publish(self._debug_make_event("debug_gps_mode", this_mode, priority=9))
			self._mode_timer = time.time()
		self._last_mode = this_mode

		# Events for location changes
		this_location = None
		if this_mode > 1:
			this_location = {
					"lat": raw["lat"],
					"lon": raw["lon"]
				}
		if type(this_location) != type(self._last_location): # Location fixed or lost
			self.publish(self._debug_make_event("debug_gps_location", this_location))
			self._location_timer = time.time()
		elif this_location is not None and distance.vincenty((this_location["lat"], this_location["lon"]), (self._last_location["lat"], self._last_location["lon"])).meters > 20.0: # Location changed too much
			self.publish(self._debug_make_event("debug_gps_jump", this_location, priority=5))
			self._location_timer = time.time()
		elif self._location_timer is None:
			self._location_timer = time.time()
		elif self._location_timer + self._debug_interval < time.time():
			self.publish(self._debug_make_event("debug_gps_location", this_location, priority=9))
			self._location_timer = time.time()
		self._last_location = this_location

	def _debug_make_event(self, event_type, value, priority=None):
		event = self.make_event_with_raw_data(value)
		event.data["event"] = event_type
		if type(priority) == type(9):
			event.priority = priority
		log.debug("debug event type: " + event_type)
		return event
		

