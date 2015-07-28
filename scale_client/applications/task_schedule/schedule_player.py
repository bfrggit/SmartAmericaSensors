from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent
from schedule_loader import ScheduleLoader
from task_schedule import TaskSchedule

import copy
import re
from threading import Lock

import logging
log = logging.getLogger(__name__)

class SchedulePlayer(Application):
	def __init__(self, broker, debug=False):
		super(SchedulePlayer, self).__init__(broker)

		self._cws = None
		self._cws_lock = Lock()
		
		self._debug_flag = debug
	
	# Functionality NOT implemented
	#TODO: Periodically check the task in progress via method calls

	def on_event(self, event, topic):
		# Ignore events from database
		if hasattr(event, "db_record"):
			return

		et = event.get_type()
		ed = event.get_raw_data()

		# Check if event is a command
		if et == "cmd_schedule_drop":
			with self._cws_lock:
				if isinstance(self._cws, TaskSchedule):
					evtls = []
					evtls += self._cws.drop()
					for evt in evtls:
						self.publish(evt)
				self._cws = None
		else:
			# Command not recognized
			# Probably this command is NOT for self
			pass
		if re.match("cmd", et) is not None:
			return

		if et == "obj_schedule_loaded":
			with self._cws_lock:
				if not isinstance(ed, TaskSchedule):
					log.error("unexpected data type for loaded schedule")
				elif self._cws is not None:
					if self._debug_flag:
						debug_e = SensedEvent(
								sensor="splayer",
								priority=4,
								data={"event": "debug_schedule_load_failure_2", "value": ed.get_name()}
							)
						self.publish(debug_e)
				else:
					if self._debug_flag:
						debug_e = SensedEvent(
								sensor="splayer",
								priority=4,
								data={"event": "debug_schedule_load_success", "value": ed.get_name()}
							)
						self.publish(debug_e)
					evtls = []
					self._cws = copy.copy(ed)
					evtls += self._cws.start()
					cwt = self._cws.get_cwt()
					if cwt is not None:
						evtls += cwt.on_start()
					else:
						self._cws = None
					for evt in evtls:
						self.publish(evt)

		# Handle event to task for listener check
		with self._cws_lock:
			if self._cws is None:
				return
			evtls = []
			cwt = self._cws.get_cwt()
			if cwt is None:
				self._cws = None
			elif cwt.listener_check(event):
				evtls += cwt.on_complete()
				evtls += self._cws.proceed()
				cwt = self._cws.get_cwt()
				if cwt is not None:
					evtls += cwt.on_start()
				else:
					self._cws = None
			for evt in evtls:
				self.publish(evt)

