from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import time
import copy
import yaml
import re
from threading import Lock
from geopy import distance

import logging
log = logging.getLogger(__name__)

class GPSGeofence(Application):
	"""
	GPSGeofence should listen to events published by GPS, and generate geofence events.
	Meanwhile, it should also listen to command events published by other components.

	It should NOT listen to LocationManager,
		because LocationManager may opt NOT to report location updates.
	
	It depends on configuration files for information of spots.
	"""
	def __init__(self, broker, config=None, debug=False):
		super(GPSGeofence, self).__init__(broker)

		self._target = None # Set geofence on this target
		self._tcount = None
		self._t_lock = Lock() # Mutex access to self._target and self._tcount

		self._debug_flag = debug
		
		# Load configuration file and push spots (targets) into a dict
		# A spot (target) configuration should contain information about
		#	Identifier as str
		#	Center coordinates (lat, lon)
		#	Radius as float
		#	Direction flag (+1 for inside, -1 for outside) as int
		self._spots = dict()
		self._spot_names = []
		if type(config) == type(""):
			try:
				with open(config) as cfile:
					cfg = yaml.load(cfile)
					if type(cfg) != type({}):
						raise TypeError
					for key in cfg:
						if type(key) != type(""):
							raise TypeError
						if type(cfg[key]) != type({}):
							raise ValueError
						if not "lat" in cfg[key] or not "lon" in cfg[key] or not "i_radi" in cfg[key] or not "o_radi" in cfg[key]:
							log.warning("Incorrect format for target: " + key)
							continue
						self._spots[key + "I"] = {"lat": cfg[key]["lat"], "lon": cfg[key]["lon"], "radius": cfg[key]["i_radi"], "d_flag": +1}
						self._spots[key + "O"] = {"lat": cfg[key]["lat"], "lon": cfg[key]["lon"], "radius": cfg[key]["o_radi"], "d_flag": -1}
						self._spot_names.append(key)
			except IOError as e:
				log.error("Error reading config file: %s" % e)
			except (TypeError, ValueError):
				log.error("Error parsing config file")
		elif config is None:
			log.warning("No config file is identified")
		else:
			log.error("Error reading config file")
		self._spot_names.sort()

	SOURCE_SUPPORT = ["gps"]


	def on_event(self, event, topic):
		# Ignore events from database
		if hasattr(event, "db_record"):
			return

		et = event.get_type()
		ed = event.get_raw_data()

		# Check if event is a command
		if et == "cmd_geofence_set":
			with self._t_lock:
				if self._target is None and type(ed) == type("") and ed in self._spots:
					self._target = ed
					log.info("geofence target set: %s" % ed)
					if self._debug_flag:
						debug_e = SensedEvent(
								sensor="geofence",
								data={"event": "debug_geofence_set", "value": ed},
								priority=5
							)
						self.publish(debug_e)
				else:
					log.warning("undefined geofence target")
					if self._debug_flag:
						debug_e = SensedEvent(
								sensor="geofence",
								data={"event": "debug_geofence_set_failure", "value": ed},
								priority=4
							)
						self.publish(debug_e)
		elif et == "cmd_geofence_reset":
			with self._t_lock:
				self._target = None
				self._tcount = None
				log.info("geofence target reset")
				if self._debug_flag:
					debug_e = SensedEvent(
							sensor="geofence",
							data={"event": "debug_geofence_reset", "value": None},
							priority=5
						)
					self.publish(debug_e)
		elif et == "cmd_geofence_list":
			list_e = SensedEvent(
					sensor="geofence",
					data={"event": "debug_geofence_list", "value": self._spot_names},
					priority=7
				)
			self.publish(list_e)
		else:
			# Command not recognized
			# Probably this command is NOT for self
			pass
		if re.match("cmd", et) is not None:
			return

		# Check if event contains geo-coordinates
		if self._target is None:
			return
		if not et in self.SOURCE_SUPPORT or not type(ed) == type({}):
			return
		with self._t_lock:
			tt = self._spots[self._target]
			if distance.vincenty((tt["lat"], tt["lon"]), (ed["lat"], ed["lon"])).meters * tt["d_flag"] < tt["radius"] * tt["d_flag"]: # Geofence trigger
				if type(self._tcount) != type(9):
					self._tcount = 0
				self._tcount += 1
				if self._tcount > 4: # Geofence event
					# Generate and publish event
					trigger_e = SensedEvent(
							sensor="geofence",
							data={"event": "geofence_trigger", "value": self._target},
							priority=5
						)
					self.publish(trigger_e)

					self._target = None
					self._tcount = None
			else: # Geofence reset
				self._tcount = 0


