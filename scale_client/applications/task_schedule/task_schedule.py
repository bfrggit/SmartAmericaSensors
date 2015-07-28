import logging
log = logging.getLogger(__name__)

class TaskItem:
	def __init__(self):
		pass
	
	def on_start(self):
		"""
		Called on start.
		Return a list of SensedEvent.
		Can be used to cast commands to other applications.
		"""
		evtls = []
		return evtls
	
	def on_complete(self):
		"""
		Called on complete.
		Return a list of SensedEvent.
		Can be used to cast messages to other applications.
		"""
		evtls = []
		return evtls
	
	def on_no_response(self):
		"""
		Called periodically when task is in progress.
		Return a list of SensedEvent.
		Can be used to cast requests to other applications.
		"""
		evtls = []
		return evtls
	
	def on_drop(self):
		evtls = []
		return evtls
	
	def listener_check(self, event):
		"""
		Called on event.
		Check if task has been completed.
		"""
		raise NotImplementedError

from scale_client.core.sensed_event import SensedEvent

from threading import Lock

class TaskSchedule:
	def __init__(self, label=None):
		if type(label) != type(""):
			label = "UNNAMED"
		self._label = label

		self._tasks = []
		self._cwt = -1 #Index only
		self._cwt_lock = Lock()

	def get_label(self):
		return self._label

	def get_name(self):
		return self.get_label()
	
	def get_len(self):
		return len(self._tasks)

	def append(self, item):
		if not isinstance(item, TaskItem):
			raise TypeError
		self._tasks.append(item)

	def start(self):
		evtls = []
		log.info("schedule started")
		evtls.append(
				SensedEvent(
						sensor="schedule",
						priority=5,
						data={"event": "debug_schedule_started", "value": self._label}
					)
			)
		evtls += self._on_start()
		evtls += self.proceed()
		return evtls
	
	def restart(self):
		evtls = []
		evtls += self.drop()
		evtls += self.start()
		return evtls
	
	def drop(self):
		evtls = []
		with self._cwt_lock:
			evtls += self._tasks[self._cwt].on_drop()
			self._cwt = -1
			log.info("schedule dropped")
			evtls += self._on_drop()
		evtls.append(
				SensedEvent(
						sensor="schedule",
						priority=5,
						data={"event": "debug_schedule_dropped", "value": self._label}
					)
			)
		return evtls

	def proceed(self):
		evtls = []
		with self._cwt_lock:
			self._cwt += 1
			if self._cwt > len(self._tasks) - 1:
				self._cwt = -1
				log.info("schedule completed")
				evtls += self._on_complete()
				evtls.append(
						SensedEvent(
								sensor="schedule",
								priority=5,
								data={"event": "debug_schedule_completed", "value": self._label}
							)
					)
		return evtls
		
	def get_cwt(self):
		with self._cwt_lock:
			if self._cwt < 0 or self._cwt > len(self._tasks) - 1:
				if not self._cwt < 0:
					log.warning("current working task index out of range")
				else:
					log.info("empty or completed schedule")
				return None
			return self._tasks[self._cwt]
		
	def _on_start(self):
		evtls = []
		return evtls
	
	def _on_complete(self):
		evtls = []
		return evtls
	
	def _on_drop(self):
		evtls = []
		return evtls

