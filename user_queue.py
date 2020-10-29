import config

class QueueElement:
    tag = ""
    lab = 0
    prior = 0

    def __init__(self, tag, lab, prior):
        self.tag = tag
        self.lab = lab
        self.prior = prior

    def __str__(self):
        name = config.USERS.get(self.tag)
        if name is None: raise ValueError("The tag \"" + self.tag + "\" is not present in the registry")

        line1 = name + " \\(@" + self.tag + "\\)\n"
        line2 = "*Лаба*: " + str(self.lab) + "\n"
        line3 = "*Рейтинг на PCMS*: " + str(self.prior) + "\n"

        return line1 + line2 + line3

class RecordQueryResult:
    index = 0
    found_with_same_priority = False

    def __init__(self, index, found_with_same_priority):
        self.index = index
        self.found_with_same_priority = found_with_same_priority

class Queue:
    mem = []

    def __iter__(self):
        return QueueIterator(self)

    def __init__(self):
        self.mem = []

    def record_present(self, tag, lab, prior):
        for i in range(len(self.mem)):
            e = self.mem[i]
            if e.tag == tag and e.lab == lab:
                found_with_same_priority = (e.prior == prior)
                return RecordQueryResult(i, found_with_same_priority)

        return None

    def remove(self, tag, lab):
        query = self.record_present(tag, lab, 0)
        if query is None: raise ValueError("the record with tag \"" + tag + "\" and lab " + str(lab) + " is not present")
        return self.mem.pop(query.index)

    def push(self, x):
        if not isinstance(x, QueueElement): 
            raise TypeError("the `other` argument wasn't an instance of `QueueElement`")

        self.mem.append(x)
        self.mem.sort(key = lambda x: (x.lab, -x.prior))

class QueueIterator:
    orig = Queue()
    i = 0

    def __init__(self, orig):
        self.orig = orig
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.i == len(self.orig.mem): raise StopIteration
        res = self.orig.mem[self.i]
        self.i += 1
        return res

