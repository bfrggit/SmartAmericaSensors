from task_schedule import TaskItem
from scale_client.core.sensed_event import SensedEvent

class SpeedTestTask(TaskItem):
	def __init__(self, methods):
		TaskItem.__init__(self)

		if type(methods) != type([]):
			raise TypeError
		self._methods = methods

	def on_start(self):
		evtls = []
		if len(self._methods) > 0:
			evt_0 = SensedEvent(
					sensor="task",
					priority=5,
					data={"event": "debug_prompt", "value": "STAY in range for a few minutes for speed tests."}
				)
			evtls.append(evt_0)
		else:
			evt_0 = SensedEvent(	
					sensor="task",
					priority=7,
					data={"event": "debug_prompt", "value": "IGNORE this. No speed test is enabled."}
				)
			evtls.append(evt_0)
		if "mqtt" in self._methods:
			evt_1 = SensedEvent(
					sensor="task",
					priority=4,
					data={"event": "cmd_mqtt_speed_test", "value": True}
				)
			evtls.append(evt_1)
		return evtls
	
	def on_complete(self):
		evtls = []
		return evtls
	
	def listener_check(self, event):
		#et = event.get_type()
		#ed = event.get_raw_data()
		#
		return True

