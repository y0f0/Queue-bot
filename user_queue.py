import config
from lab_table_loader import get_user_rating, LeaderboardLabError, LeaderboardUserError

class QueueElement:
    tag = ""
    lab = 0

    def __init__(self, tag, lab):
        self.tag = tag
        self.lab = lab

    def __str__(self):
        name = config.USERS.get(self.tag)
        if name is None: raise ValueError("The tag \"" + self.tag + "\" is not present in the registry")

        try:
            rating = get_user_rating(self.tag, self.lab) 
        except ValueError as err: print("[QEUE_PRINTING_ROUTINE] " + str(err))
        except LeaderboardLabError as err: print("[QEUE_PRINTING_ROUTINE] " + str(err))
        except LeaderboardUserError as err: print("[QEUE_PRINTING_ROUTINE] " + str(err))
        except: print("[QUEUE_PRINTING_ROUTINE] Uexpcted error")
        
        if rating is None: return "BAD_DATA\n"
        
        line1 = name + " (@" + self.tag + ")\n"
        line2 = "<b>Лаба</b>: " + str(self.lab) + "\n"
        line3 = "<b>Рейтинг на PCMS</b>: " + str(rating) + "\n"
        return line1 + line2 + line3

    def key(self):
        try:
            rating = get_user_rating_silent(self.tag, self.lab)
            return (self.lab, rating)
        except:
            return (self.lab, 10**100)

class RecordQueryResult:
    index = 0

    def __init__(self, index):
        self.index = index

class Queue:
    mem = []

    def __iter__(self):
        return QueueIterator(self)

    def __init__(self):
        self.mem = []

    def record_present(self, tag, lab):
        for i in range(len(self.mem)):
            e = self.mem[i]
            if e.tag == tag and (lab is None or e.lab == lab):
                return RecordQueryResult(i)

        return None

    def remove(self, tag, lab):
        query = self.record_present(tag, lab)
        if query is None: raise ValueError("the record with tag \"" + tag + "\" and lab " + str(lab) + " is not present")
        return self.mem.pop(query.index)

    def balance(self):
        self.mem.sort(key = lambda x: x.key())

    def push(self, x):
        if not isinstance(x, QueueElement): 
            raise TypeError("the `other` argument wasn't an instance of `QueueElement`")

        _ = get_user_rating(x.tag, x.lab)

        self.mem.append(x)
        self.balance()

    def dump(self, f):
        for x in self: 
            f.write(str(x.tag) + " " + str(x.lab) + "\n")

    def load(self, f):
        for l in f:
            l = l.strip()
            elems = l.split()
            if len(elems) != 2: 
                print("[QUEUE_RECOVER_ROUTINE] line \"" + l + "\" discarded (weird element amount)") 
                continue
            tag = elems[0]
            try:
                lab = int(elems[1])
            except:
                print("[QUEUE_RECOVER_ROUTINE] line \"" + l + "\" discarded (failed to parse lab number)")
                continue
            try:
                self.push(QueueElement(tag, lab))
            except ValueError as err: print("[QEUE_RECOVER_ROUTINE] line \"" + l + "\" discarded (" + str(err) + ")")
            except LeaderboardLabError as err: print("[QUEUE_RECOVER_ROUTINE] line \"" + l + "\" discarded (" + str(err) + ")")
            except LeaderboardUserError as err: print("[QUEUE_RECOVER_ROUTINE] line \"" + l + "\" discarded (" + str(err) + ")")
            except: print("[QUEUE_RECOVER_ROUTINE] line \"" + l + "\" discarded (Uexpected error)")

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

