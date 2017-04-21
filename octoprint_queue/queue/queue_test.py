from unittest import TestCase
from octoprint_queue.queue import PrintQueue, QueueItem

q = PrintQueue(
    [], 0, 'stopped'
).add_item(
    QueueItem("1", "one"),
).add_item(
    QueueItem("2", "two"),
).add_item(
    QueueItem("3", "three"),
)


class TestPrintQueue(TestCase):
    def test_addItem(self):
        self.assertEqual(
            q,
            PrintQueue(
                items=[QueueItem("1", "one"), QueueItem("2", "two"), QueueItem("3", "three")],
                cursor=0,
                status='stopped'
            )
        )

    def test_rm_item(self):
        # removing and item before the cursor deletes the item and
        # moves the cursor

        self.assertEqual(
            q.set_cursor(1).rm_item(0),
            PrintQueue(
                items=[QueueItem("2", "two"), QueueItem("3", "three")],
                cursor=0,
                status='stopped'
            )
        )

        # removing and item at the cursor deletes the item and the
        # cursor moves to the next item
        self.assertEqual(
            q.set_cursor(1).rm_item(1),
            PrintQueue(
                items=[QueueItem("1", "one"), QueueItem("3", "three")],
                cursor=1,
                status='stopped'
            )
        )

        # removing and item after the cursor deletes the item
        # and the cursor continues to point at the item prior to the remove
        self.assertEqual(
            q.set_cursor(1).rm_item(2),
            PrintQueue(
                items=[QueueItem("1", "one"), QueueItem("2", "two")],
                cursor=1,
                status='stopped'
            )
        )

    def testPassItem(self):
        # passing the item before the end moves it to the next item
        self.assertEqual(
            q.pass_item(),
            PrintQueue(
                items=q.items,
                cursor=1,
                status='stopped'
            )
        )

        self.assertEqual(
            q.set_cursor(2).pass_item(),
            PrintQueue(
                items=q.items,
                cursor=0,
                status='stopped'
            )
        )
