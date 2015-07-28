from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent
from task_schedule import *

import copy
import yaml
import re
import os
from threading import Lock

import logging
log = logging.getLogger(__name__)

class ScheduleLoader(Application):
	"""
	ScheduleLoader load pre-configured schedules from configuration.
	It should also define some simple schedule examples for demonstration.
	"""
	def __init__(self, broker, config_dir=None, debug=False):
		super(ScheduleLoader, self).__init__(broker)

		self._schedules = dict()
		self._config_dir = config_dir
		self._debug_flag = debug

		self._populate_demos()
	
	def _populate_demos(self):
		schdl_0 = TaskSchedule()
		self._schedules["EMPTY"] = schdl_0
		self._schedules["BLANK"] = schdl_0
		
		from wait_for_rf_message_task import WaitForRFMessageTask

		schdl_1 = TaskSchedule("HELLO")
		schdl_1.append(WaitForRFMessageTask("Hello"))
		self._schedules["HELLO"] = schdl_1

		from wait_for_heartbeat_task import WaitForHeartbeatTask

		schdl_2 = TaskSchedule("HB")
		schdl_2.append(WaitForHeartbeatTask())
		self._schedules["HB"] = schdl_2

		from no_task import NoTask

		schdl_3 = TaskSchedule("NO")
		schdl_3.append(NoTask())
		self._schedules["NO"] = schdl_3

	def _load_config(self, config_dir):
		if type(config_dir) != type(""):
			return

		"""
		Load and parse configuration file and push schedules into a dict
		"""
		fl = None
		try:
			fl = os.listdir(config_dir)
		except TypeError:
			return
		except OSError:
			log.warning("cannot access configuration directory")
		if type(fl) != type([]):
			return

		from wait_for_rf_message_task import WaitForRFMessageTask
		from geofence_task import GeofenceTask
		from internet_access_task import InternetAccessTask

		for f in fl:
			if f.endswith(".schedule.yml"):
				fp = os.path.join(config_dir, f)
				try:
					with open(fp) as cfile:
						cfg = yaml.load(cfile)
						if type(cfg) != type(dict()):
							raise TypeError
						if not "id" in cfg or not "schedule" in cfg:
							raise ValueError
						if type(cfg["id"]) != type("") or type(cfg["schedule"]) != type([]):
							raise TypeError
						if cfg["id"] in self._schedules:
							log.error("schedule identifier conflicts with existing record")
							raise ValueError
						schdl_t = TaskSchedule(cfg["id"])
						for li in cfg["schedule"]:
							if type(li) != type(dict()):
								log.warning("invalid list item type, should be dict")
								continue
							if not "type" in li:
								log.warning("invalid list item, missing task type")
								continue
							if li["type"] == "input":
								if not "text" in li or type(li["text"]) != type(""):
									log.warning("invalid input task, missing text")
								else:
									schdl_t.append(WaitForRFMessageTask(li["text"]))
							elif li["type"] == "geofence":
								if not "target" in li or type(li["target"]) != type(""):
									log.warning("invalid geofence task, missing target")
								else:
									schdl_t.append(GeofenceTask(li["target"]))
							elif li["type"] == "internet":
								schdl_t.append(InternetAccessTask())
							else:
								log.warning("invalid list item, unknown task type")
						self._schedules[cfg["id"]] = schdl_t
				except IOError as e:
					log.error("Error reading config file: %s" % e)
				except (TypeError, ValueError):
					log.error("Error parsing config file")
	
	def on_start(self):
		super(ScheduleLoader, self).on_start()

		self._load_config(self._config_dir)

	def _get_schedule(self, sname):
		if sname in self._schedules:
			return self._schedules[sname]
		else:
			return None
	
	def _get_schedule_names(self):
		return sorted(list(self._schedules))

	def _get_schedule_names_2(self):
		ls = self._get_schedule_names()
		for j in xrange(0, len(ls)):
			ls[j] += " (%d)" % self._schedules[ls[j]].get_len()
		return ls
	
	def on_event(self, event, topic):
		# Ignore events from database
		if hasattr(event, "db_record"):
			return

		et = event.get_type()
		ed = event.get_raw_data()

		# Check if event is a command
		if et == "cmd_schedule_list":
			list_e = SensedEvent(
					sensor="sloader",
					priority=7,
					data={"event": "debug_schedule_list", "value": self._get_schedule_names_2()}
				)
			self.publish(list_e)
		elif et == "cmd_schedule_load":
			if type(ed) != type(""):
				log.error("unexpected data type in command with type: " + et)
			else:
				schdl = self._get_schedule(ed)
				if not isinstance(schdl, TaskSchedule):
					log.warning("undefined schedule name")
					if self._debug_flag:
						debug_e = SensedEvent(
								sensor="sloader",
								priority=4,
								data={"event": "debug_schedule_load_failure", "value": ed}
							)
						self.publish(debug_e)
					
				else:
					load_e = SensedEvent(
							sensor="sloader",
							priority=5,
							data={"event": "obj_schedule_loaded", "value": copy.copy(schdl)}
						)
					self.publish(load_e)
		else:
			# Command not recognized
			# Probably this command is NOT for self
			pass
		if re.match("cmd", et) is not None:
			return
		
