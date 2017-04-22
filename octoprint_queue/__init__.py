# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
from octoprint_queue.queue import PrintQueue, QueueItem
from gpiozero import Button, LED, pi_info

from flask import jsonify, request, redirect, url_for
from pprint import pformat
import json
import os

try:
        pi_info()
        IS_PI = True
except:
        IS_PI = False

class QueuePlugin(octoprint.plugin.AssetPlugin,
                  octoprint.plugin.BlueprintPlugin,
                  octoprint.plugin.SettingsPlugin,
                  octoprint.plugin.EventHandlerPlugin,
                  octoprint.plugin.TemplatePlugin):

        def get_settings_defaults(self):
                return {
                        'button_pin': 21,
                        'led_pin': 3
                }

        def initialize(self):
                self.q = PrintQueue([], 0, 'stopped')
                self.q_path = os.path.join(
                        self.get_plugin_data_folder(),
                        'q.json'
                )
                self.load_q()
                self._logger.info("__init__".format(self.q))
                self.init_physical()

        def init_physical(self):
                if IS_PI:
                        self.led = LED(
                                self._settings.get_int(['led_pin'])
                        )
                        self.button = Button(
                                self._settings.get_int(['button_pin'])
                        )
                        self.button.when_released = self.on_button

        def update_physical(self, q1, q2):
                if IS_PI:
                        if q2.status == 'paused':
                                self.led.blink()
                        elif q2.status == 'running':
                                self.led.on()
                        else:
                                self.led.off()

        def on_button(self):
                if self.q.status in ('paused', 'stopped'):
                        self.sync(
                                self.q.set_status('running')
                        )

        def print_item(self, q, printAfterSelect=True):
                item = q.current_item
                if item and self._printer.is_ready():
                        self._printer.select_file(
                                self._file_manager.path_on_disk('local', item.name),
                                printAfterSelect=printAfterSelect,
                                sd=False # not supported yet
                        )

        def on_event(self, event, payload):
                if event in ('PrintFailed', 'PrintCancelled'):
                        self.on_print_failed()
                elif event in ('PrintDone'):
                        self.on_print_finished()
                elif event in ('PrintStarted'):
                        self.on_print_started()

        def on_print_failed(self):
                self.sync(
                        self.q.set_status('stopped')
                )

        def on_print_started(self):
                if self.q.status == 'paused':
                        self.sync(
                                self.q.set_status('running')
                        )
                else: # someone started a non-queue item
                        self.sync(
                                self.q.set_status('stopped')
                        )

        def on_print_finished(self):
                if self.q.status == 'running':
                        self.sync(
                                self.q.set_status('paused')
                        )

        def load_q(self):
                if os.path.exists(self.q_path):
                        with open(self.q_path) as fh:
                                data = json.load(fh)
                else:
                        data = {}


                self.q = self.q._replace(
                        cursor=data.get('cursor', 0),
                        items=[
                                QueueItem.from_json(x)
                                for x in data.get('items', [])
                        ]
                )

        def save_q(self):
                data = self.q.json
                with open(self.q_path, "w") as fh:
                        json.dump(data, fh)

        def sync(self, q):
                # start the queue if the status goes from stopped or paused to running
                self._logger.info("From {}".format(pformat(self.q)))
                self._logger.info("To {}".format(pformat(q)))

                if self.q.status in ('stopped', 'paused') and q.status == 'running':
                # start printing the currently selected item
                        self.print_item(q)
                # moving from running to paused, we select the next item
                elif self.q.status == 'running' and q.status == 'paused':
                        q = q.proceed()
                        self.print_item(q, printAfterSelect=False)

                self.update_physical(self.q, q)

                # update the q
                self.q = q
                self.save_q()
                self._logger.info("PrinterStateChanged")
                self._event_bus.fire('PrinterStateChanged')

	##~~ BlueprintPlugin mixin
        @octoprint.plugin.BlueprintPlugin.route("/q", methods=["GET"])
        def REST_q(self):
                def bind_item(i, item):
                        item['@id'] = url_for('plugin.queue.REST_q_rm_item', i=i)
                        item['@methods'] = ['DELETE']
                        return item

                json = self.q.json
                json['@id'] = url_for('plugin.queue.REST_q')
                json['items'] = [bind_item(i, x) for i, x in enumerate(json['items'])]
                return jsonify(json)

        @octoprint.plugin.BlueprintPlugin.route("/q/items", methods=["POST"])
        def REST_q_add_item(self):
                item = QueueItem(
                        key=request.json.get('key', ''),
                        name=request.json.get('name', '')
                )

                self.sync(
                        self.q.add_item(item)
                )
                return redirect(url_for('plugin.queue.REST_q'), code=303)

        @octoprint.plugin.BlueprintPlugin.route("/q/items/<int:i>", methods=["DELETE"])
        def REST_q_rm_item(self, i):
                self.sync(
                        self.q.rm_item(i)
                )
                return redirect(url_for('plugin.queue.REST_q'), code=303)

        @octoprint.plugin.BlueprintPlugin.route("/q/cursor", methods=["PUT"])
        def REST_q_set_cursor(self):
                self.sync(
                        self.q.set_cursor(request.json)
                )
                return redirect(url_for('plugin.queue.REST_q'), code=303)

        @octoprint.plugin.BlueprintPlugin.route("/q/status", methods=["PUT"])
        def REST_q_set_status(self):
                self.sync(
                        self.q.set_status(request.json)
                )
                return redirect(url_for('plugin.queue.REST_q'), code=303)

        @octoprint.plugin.BlueprintPlugin.route("/q/button", methods=["POST"])
        def REST_q_button(self):
                self.on_button()
                return redirect(url_for('plugin.queue.REST_q'), code=303)


        ##~~ TemplatePlugin mixin
        def get_template_configs(self):
                return [
                        dict(type="sidebar", name="Print Queue", icon="sort-by-attributes-alt"),
                ]

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/queue.js"],
			css=["css/queue.css"],
			less=["less/queue.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			queue=dict(
				displayName="Queue Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="ericmoritz",
				repo="OctoPrint-Queue",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/ericmoritz/OctoPrint-Queue/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Queue Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = QueuePlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
