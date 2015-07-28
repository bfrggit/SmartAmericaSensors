from task_schedule import TaskItem
from scale_client.core.sensed_event import SensedEvent

class GeofenceTask(TaskItem):
	def __init__(self, target):
		TaskItem.__init__(self)

		if type(target) != type(""):
			raise TypeError
		self._target = target
	
	def on_start(self):
		evtls = []
		evt_0 = SensedEvent(
				sensor="task",
				priority=5,
				data={"event": "debug_prompt", "value": "PLEASE trigger target: %s" % self._target}
			)
		evt_1 = SensedEvent(
				sensor="task",
				priority=4,
				data={"event": "cmd_geofence_set", "value": self._target}
			)
		evtls.append(evt_0)
		evtls.append(evt_1)
		return evtls
	
	def listener_check(self, event):
		et = event.get_type()
		ed = event.get_raw_data()

		if et != "geofence_trigger":
			return False
		if ed != self._target:
			return False
		return True

