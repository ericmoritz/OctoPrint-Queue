/*
 * View model for OctoPrint-Queue
 *
 * Author: Eric Moritz
 * License: AGPLv3
 */
$(function() {
    function QueueItem(i, key, name) {
        var self = this;
        self.i = i;
        self.key = key;
        self.name = name;
    }

    function QueueViewModel(parameters) {
        var self = this;

        self.filesViewModel = parameters[0];

        self.items = ko.observableArray([]);

        self.cursor = ko.observable(0);

        self.rm_item = function(index) {
        };

        self.updateState = function() {
            $.ajax({
                url: '/plugin/queue/q',
                type: 'GET'
            }).done(function(data) {
                console.log(data);
                self.cursor(data.cursor);
                self.items.removeAll();
                data.items.forEach(function(x, i) {
                    self.items.push(
                        new QueueItem(i, x.key, x.name)
                    );
                });
            });
        };

        self.rmItem = function(item) {
            console.log("removing " + item.i);
            $.ajax({
                url: '/plugin/queue/q/items/' + item.i,
                type: 'DELETE'
            }).done(function() {
                self.updateState();
            });
        };

        self.addItem = function(key, name) {
            console.log("adding " + name);
            $.ajax({
                url: '/plugin/queue/q/items',
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json; charset=UTF-8',
                data: JSON.stringify({
                    'key': key,
                    'name': name
                })
            }).done(function() {
                self.updateState();
            });
        };

        self.setStatus = function() {
            $.ajax({
                url: '/plugin/queue/q/status',
                type: 'PUT',
                dataType: 'json',
                contentType: 'application/json; charset=UTF-8',
                data: JSON.stringify('start')
            });
        }

        // hack the file listing
        self.hackTimer = window.setInterval(function() {
            $('#files .gcode_files .machinecode').each(function(i) {
                var key = $(this).attr('id');
                var btn = $($('#add_to_queue_btn_tmpl').html());
                var exists = $(this).find('.btn-add-to-queue').length > 0;
                var buttons = $(this).find('.action-buttons');
                var name = $(this).find('.title').text();
                if (self.filesViewModel.currentPath() != '') {
                    name = [self.filesViewModel.currentPath(), name].join('/');
                }

                btn.click(function() {
                    self.addItem(key, name)
                });
                if (!exists) {
                    buttons.append(btn);
                }
            });
        }, 250);

        // initialize
        self.updateState();
    }


    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push({
        construct: QueueViewModel,
        elements: ['#queue_sidebar'],
        dependencies: ['filesViewModel']
    });
});
