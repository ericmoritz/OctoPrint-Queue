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
from flask import jsonify, request, redirect, url_for

class QueuePlugin(octoprint.plugin.AssetPlugin,
                  octoprint.plugin.BlueprintPlugin,
                  octoprint.plugin.TemplatePlugin):

        def __init__(self):
                self.q = PrintQueue([], 0, 'stopped')

        def _startQ(self):
                print "starting q!"

        def sync(self, q):
                # start the queue if the status goes from stopped to running
                if self.q.status == 'stopped' and q.status == 'running':
                        self._startQ()

                # update the q
                self.q = q

                # TODO store the Q somewhere

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
