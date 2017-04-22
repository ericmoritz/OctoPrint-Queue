# OctoPrint-Queue

**Work in progress**

This plugin will add a print queue to your sidebar that you can load files to.

When a print finishes, you will remove the print and press the success
button to tell the plugin to proceed with the next item in the queue.

This plugin has optional support for an external button wired to the
raspberry PI's GPIO pins.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/ericmoritz/OctoPrint-Queue/archive/master.zip

## Physical UI

You can utilized a button and LED for quickly advancing the queue when
a print is done.

You can connect a button to pin 21 and an LED (with a pull down
resistor) to pin 3.  When the queue is running the LED will be solid
and when the queue is waiting, the LED will blink.

Once you've cleared the print bed, press the button and the next item
in the queue will start.
