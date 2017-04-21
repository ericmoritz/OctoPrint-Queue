from collections import namedtuple

class QueueItem(namedtuple("QueueItem", ["key", "name"])):
    @property
    def json(self):
        return {
            "key": self.key,
            "name": self.name
        }

PrintQueueBase = namedtuple("PrintQueueBase", ["items", "cursor", "status"])

class PrintQueue(PrintQueueBase):
    def add_item(self, item):
        return self._replace(
            items=(self.items[:] + [item]),
            cursor=self.cursor
        )

    def rm_item(self, index):
        """

        """
        mod = 0
        if index < self.cursor:
            mod = -1

        return self._replace(
            items = self.items[0:index] + self.items[index+1:],
            cursor = self.cursor + mod
        )

    def pass_item(self):
        """

        """
        if self.cursor == len(self.items) - 1:
            return self._replace(
                cursor = 0
            )
        else:
            return self._replace(
                cursor = self.cursor + 1
            )

    def set_cursor(self, i):
        return self._replace(
            cursor=i
        )

    def set_status(self, status):
        return self._replace(
            status=status
        )

    @property
    def json(self):
        return {
            "cursor": self.cursor,
            "items": [x.json for x in self.items]
        }
