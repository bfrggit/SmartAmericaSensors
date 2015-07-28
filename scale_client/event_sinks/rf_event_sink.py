from scale_client.event_sinks.event_sink import EventSink

import json
import time
import threading
import logging
log = logging.getLogger(__name__)
#log.setLevel(logging.INFO)


class RFEventSink(EventSink):
	def __init__(self, broker, tty_path=None, sleep=0):
		super(RFEventSink, self).__init__(broker)
		if not tty_path or type(tty_path) != type(""):
			raise TypeError
		self._dev_path = tty_path
		self._dev_name = tty_path.split("/")[-1]
		self._sleep = sleep
		self._rfca = False
		self._rf_lock = threading.Lock()

		self._encoders = dict()
		self._register_encoders()

	def send(self, eets):
		if not eets or not type(eets) == type(()) or len(eets) != 2:
			return

		time_x, encoded_event = eets
		time_f = time.time()
		timestamp = time.strftime("%H:%M:%S", time.localtime(time_f))
		time_diff = " "
		if time_x is not None:
			time_diff = " %+d " % round((time_x - time_f) * 1000)

		msg = encoded_event
		d = None
		self._rf_lock.acquire()
		try:
			d = open(self._dev_path, "r+")
			d.write(timestamp + time_diff + msg + " \r\n")
			d.close()
			log.info("messaged wrote to " + self._dev_name)
		except IOError:
			log.warning("failed writing to " + self._dev_name)
		time.sleep(self._sleep)
		self._rf_lock.release()
		#log.info(msg)

	MODE_STR = {
		0: "NO DATA",
		1: "NO FIX",
		2: "2D FIX",
		3: "3D FIX"
	}
	
	def _register_encoders(self):
		def encdr_0(et, ed):
			encoded_event = "HB"
			return encoded_event
		self._encoders["heartbeat"] = encdr_0

		def encdr_1(et, ed):
			encoded_event = None
			if ed is not None:
				self._rfca = ed
				if self._rfca:
					encoded_event = "DEV: Connected."
					log.debug("rfcomm device available")
				else:
					log.debug("rfcomm device unavailable")
			return encoded_event
		self._encoders["rfcomm_connect"] = encdr_1

		def encdr_2(et, ed):
			encoded_event = None
			if type(ed) == type(""):
				encoded_event = "ECHO: " + ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["rfcomm_message"] = encdr_2

		def encdr_3(et, ed):
			encoded_event = None
			if type(ed) == type(9):
				encoded_event = "GPS: Mode " + str(ed) + " "
				if ed in self.MODE_STR:
					encoded_event += self.MODE_STR[ed]
				else:
					encoded_event += "UNKNOWN" # Should not happen
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_gps_mode"] = encdr_3

		def encdr_4(et, ed):
			encoded_event = "LM: Location unavailable."
			if ed:
				encoded_event = "LM: Location available."
			return encoded_event
		self._encoders["debug_location_update"] = encdr_4

		def encdr_5(et, ed):
			encoded_event = None
			if type(ed) == type(""):
				encoded_event = "LM: Location expired (" + ed + ")"
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_location_expire"] = encdr_5

		def encdr_6(et, ed):
			encoded_event = None
			if type(ed) == type(""):
				if et == "debug_text":
					encoded_event = "TEXT: " + ed
				elif et == "debug_prompt":
					encoded_event = "PROMPT: " + ed
				else:
					return None # Should not happen
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_text"] = encdr_6
		self._encoders["debug_prompt"] = encdr_6

		def encdr_7(et, ed):
			encoded_event = None
			warning_flag = True
			if type(ed) == type(()):
				if len(ed) == 2 and type(ed[0]) == type(ed[1]) and type(ed[1]) == type(9):
					encoded_event = "IWLIST: %d, %d" % ed
					warning_flag = False
				elif len(ed) == 3 and type(ed[0]) == type(ed[1]) and type(ed[1]) == type(ed[2]) and type(ed[2]) == type(9):
					if ed[2] == 0:
						encoded_event = "IWLIST: %d, %d" % ed[0:2]
						warning_flag = False
					elif ed[2] > 0:
						encoded_event = "IWLIST: %d, %d (%d)" % (ed[0], ed[1] + ed[2], ed[2])
						warning_flag = False
			if warning_flag:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_iwlist_scan_count"] = encdr_7

		def encdr_8(et, ed):
			encoded_event = "CMD: Bad format."
			return encoded_event
		self._encoders["debug_cmd_bad_format"] = encdr_8

		def encdr_9(et, ed):
			encoded_event = "GF: Target reset."
			return encoded_event
		self._encoders["debug_geofence_reset"] = encdr_9

		def encdr_10(et, ed):
			encoded_event = None
			if type(ed) == type(""):
				encoded_event = "GF: Target %s triggered." % ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["geofence_trigger"] = encdr_10

		def encdr_11(et, ed):
			encoded_event = None
			if type(ed) == type([]):
				if et == "debug_geofence_list":
					encoded_event = "GF: Target list: " + " ".join(ed)
				elif et == "debug_schedule_list":
					encoded_event = "SCLDR: Schedule list: " + " ".join(ed)
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_geofence_list"] = encdr_11
		self._encoders["debug_schedule_list"] = encdr_11

		def encdr_12(et, ed):
			encoded_event = None
			if type(ed) == type(""):
				encoded_event = "GF: Target "
				if et == "debug_geofence_set_failure":
					encoded_event += "cannot set: "
				else:
					encoded_event += "set: "
				encoded_event += ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_geofence_set"] = encdr_12
		self._encoders["debug_geofence_set_failure"] = encdr_12

		def encdr_14(et, ed):
			encoded_event = None
			if type(ed) == type({}) and "lat" in ed and "lon" in ed:
				encoded_event = "GPS: " + "%.4f" % ed["lat"] + ", " + "%.4f" % ed["lon"]
				if et == "debug_gps_jump":
					encoded_event += " (?)"
			elif ed is None:
				encoded_event = "GPS: Location unavailable."
			else:
				log.warning("unrecognized data type in event object with type: " + et)
			return encoded_event
		self._encoders["debug_gps_location"] = encdr_14
		self._encoders["debug_gps_jump"] = encdr_14

		def encdr_15(et, ed):
			if type(ed) != type(9.0):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			encoded_event = "CPUT: %.3f" % ed
			return encoded_event
		self._encoders["cpu_temperature"] = encdr_15
		
		def encdr_16(et, ed):
			if type(ed) != type(9.0):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			encoded_event = "CPUF: %.3f" % ed
			return encoded_event
		self._encoders["cpu_frequency"] = encdr_16

		def encdr_17(et, ed):
			if type(ed) != type(""):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			if et == "debug_schedule_load_failure":
				encoded_event = "SCLDR"
			elif et == "debug_schedule_load_failure_2":
				encoded_event = "SCPLR"
			else:
				return None
			encoded_event += ": Schedule failed to load: " + ed
			return encoded_event
		self._encoders["debug_schedule_load_failure"] = encdr_17
		self._encoders["debug_schedule_load_failure_2"] = encdr_17
		
		def encdr_18(et, ed):
			if type(ed) != type(""):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			encoded_event = "SCPLR: Schedule loaded: " + ed
			return encoded_event
		self._encoders["debug_schedule_load_success"] = encdr_18
		
		def encdr_19(et, ed):
			if type(ed) != type(""):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			encoded_event = "SCHDL: Schedule started: " + ed
			return encoded_event
		self._encoders["debug_schedule_started"] = encdr_19
		
		def encdr_20(et, ed):
			if type(ed) != type(""):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			encoded_event = "SCHDL: Schedule dropped: " + ed
			return encoded_event
		self._encoders["debug_schedule_dropped"] = encdr_20
		
		def encdr_21(et, ed):
			if type(ed) != type(""):
				log.warning("unrecognized data type in event object with type: " + et)
				return None
			encoded_event = "SCHDL: Schedule completed: " + ed
			return encoded_event
		self._encoders["debug_schedule_completed"] = encdr_21

	def encode_event(self, event):
		et = event.get_type()
		ed = event.get_raw_data()
		log.debug("received event type: " + et)
		encoded_event = None
		timestamp = None
		eets = None

		if hasattr(event, "timestamp") and (type(event.timestamp) == type(9.0) or type(event.timestamp) == type(9)):
			timestamp = event.timestamp

		if et in self._encoders:
			encoded_event = self._encoders[et](et, ed)
			if encoded_event is not None:
				eets = (timestamp, encoded_event)
		else: # Unrecognized event
			log.debug("unrecognized event")

		return eets

	def check_available(self, event):
		et = event.get_type()
		if et == "rfcomm_connect":
			return True
		return self._rfca
