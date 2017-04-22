/*
 * View model for OctoPrint-Queue
 *
 * Author: Eric Moritz
 * License: AGPLv3
 */


$(function() {
    var Maybe = {
        Just: function(x) {
            return {
                then: function(fn) {
                    return fn(x);
                }
            };
        },

        Nothing: {
            then: function() {
                return Maybe.Nothing;
            }
        },
        liftBool: function(x) {
            return x ? Maybe.Just() : Maybe.Nothing;
        }
    };

    function QueueItem(i, key, name) {
        var self = this;
        self.i = i;
        self.key = key;
        self.name = name;
    }

    function QueueViewModel(parameters) {
        var self = this;

        self.filesViewModel = parameters[0];
        self.printerStateViewModel = parameters[1];

        self.items = ko.observableArray([]);

        self.cursor = ko.observable(0);

        self.status = ko.observable('stopped');

        self.isRunning = ko.computed(function() {
            return self.status() == 'running';
        });

        self.isStopped = ko.computed(function() {
            return self.status() == 'stopped';
        });

        self.isPaused = ko.computed(function() {
            return self.status() == 'paused';
        });

        self.isPrinterReady = ko.computed(function() {
            return (
                self.items().length > 0 &&
                self.printerStateViewModel.isReady()
            );
        });

        self.assertPrinterReady = function() {
            return Maybe.liftBool(self.isPrinterReady());
        };

        self.updateState = function() {
            return $.ajax({
                url: '/plugin/queue/q',
                type: 'GET'
            }).then(function(data) {
                console.log(data);
                self.cursor(data.cursor);
                self.status(data.status);

                self.items.removeAll();
                data.items.forEach(function(x, i) {
                    self.items.push(
                        new QueueItem(i, x.key, x.name)
                    );
                });
            });
        };

        self.selectItem = function(item) {
            console.log("selecting " + item.i);
            return $.ajax({
                url: '/plugin/queue/q/cursor',
                type: 'PUT',
                dataType: 'json',
                contentType: 'application/json; charset=UTF-8',
                data: JSON.stringify(item.i)
            }).then(function() {
                return self.updateState();
            });
        };

        self.rmItem = function(item) {
            console.log("removing " + item.i);
            $.ajax({
                url: '/plugin/queue/q/items/' + item.i,
                type: 'DELETE'
            }).then(function() {
                return self.updateState();
            });
        };

        self.addItem = function(key, name) {
            console.log("adding " + name);
            return $.ajax({
                url: '/plugin/queue/q/items',
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json; charset=UTF-8',
                data: JSON.stringify({
                    'key': key,
                    'name': name
                })
            }).then(function() {
                return self.updateState();
            });
        };

        self.proceed = function() {
            self.assertPrinterReady().then(function() {
                return self.setStatus('running');
            });
        };

        self.startQueue = function() {
            // assert the printer is connected
            // assert the printer is stopped
            self.assertPrinterReady().then(function() {
                return self.setStatus('running');
            });
        };

        self.setStatus = function(status) {
            console.log("setting status to " + status)
            return $.ajax({
                url: '/plugin/queue/q/status',
                type: 'PUT',
                dataType: 'json',
                contentType: 'application/json; charset=UTF-8',
                data: JSON.stringify(status)
            }).then(function() {
                return self.updateState();
            });
        };

        var sjs = new SockJS(SOCKJS_URI);
        sjs.onmessage = function(msg) {
            var _event = msg.data.event || {};
            if (_event.type) {
                console.log(_event);
            }
            if (_event.type == 'PrinterStateChanged') {
                self.updateState();
            }
        };


        self.timer = window.setInterval(function() {
            // hack the file listing for the add button
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

        self.updateState();
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push({
        construct: QueueViewModel,
        elements: ['#queue_sidebar'],
        dependencies: ['filesViewModel', 'printerStateViewModel']
    });
});
