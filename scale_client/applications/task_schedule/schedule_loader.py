from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent
from task_schedule import *

import copy
import yaml
import re
from threading import Lock

import logging
log = logging.getLogger(__name__)

class ScheduleLoader(Application):
	"""
	ScheduleLoader load pre-configured schedules from configuration.
	It should also define some simple schedule examples for demonstration.
	"""
	def __init__(self, broker, config=None, debug=False):
		super(ScheduleLoader, self).__init__(broker)

		self._schedules = dict()
		self._debug_flag = debug

		self._populate_demos()
		self._load_config(config)
	
	def _populate_demos(self):
		schdl_0 = TaskSchedule()
		self._schedules["EMPTY"] = schdl_0
		self._schedules["BLANK"] = schdl_0
		
		from wait_for_rf_message_task import WaitForRFMessageTask

		schdl_1 = TaskSchedule("HELLO")
		schdl_1.append(WaitForRFMessageTask("Hello"))
		self._schedules["HELLO"] = schdl_1

	def _load_config(self, config):
		if type(config) != type(""):
			return

		"""
		Load and parse configuration file and push schedules into a dict
		"""
		pass #TODO

	def _get_schedule(self, sname):
		if sname in self._schedules:
			return self._schedules[sname]
		else:
			return None
	
	def _get_schedule_names(self):
		return sorted(list(self._schedules))
	
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
					data={"event": "debug_schedule_list", "value": self._get_schedule_names()}
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
		
