from config import USERS
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError as XmlParseError

class LeaderboardLabError(Exception):
    tag = ""
    lab = 0

    def __init__(self, tag, lab):
        self.tag = tag
        self.lab = lab

    def __str__(self):
        return "Lab " + str(self.lab) + " isn't loaded"

class LeaderboardUserError(Exception):
    tag = ""
    lab = 0

    def __init__(self, tag, lab):
        self.tag = tag
        self.lab = lab

    def __str__(self):
        return "Found no rating for " + "@" + str(self.tag) + " in lab " + str(self.lab) + " table"

class LeaderboardLoadError(Exception):
    num = 0
    msg = ""

    def __init__(self, num, msg):
        self.num = num
        self.msg = msg

    def __str__(self):
        return "Failed to load lab " + str(num) + " (" + msg + ")"

# array<dict<name, prior>>
leaderboard = []

def construct_user(x):
    i, node = x
    name = node[1].text
    return i + 1, name

def compile_users(path):
    tree = ET.parse(path)
    root = tree.getroot()
    table = root[1][2][1][0][4][1]
    return map(construct_user, enumerate(iter(table)))

def load_lab_leaderboard(lab):
    global leaderboard

    print("Loading leaderboard for lab " + str(lab))
    if lab > len(leaderboard): raise ValueError("The lab under number `" + str(lab) + "` wasn't registered")

    path = "leaderboards/lab" + str(lab) + ".xml"
    try:
        it = compile_users(path)
    except XmlParseError:
        raise LeaderboardLoadError(lab, "Failed to parse the .xml file")
    except FileNotFoundError:
        raise LeaderboardLoadError(lab, "Failed to find the lab file")

    for (i, name) in it: 
        leaderboard[lab - 1][name] = i
    print("Leaderboard for lab " + str(lab) + " has been loaded")

def init_leaderboard(last_lab):
    global leaderboard

    for i in range(1, last_lab + 1):
        leaderboard.append({})
        load_lab_leaderboard(i)

def get_user_rating(username, lab):
    name = USERS.get(username)

    if name is None: raise ValueError("User @" + username + "is not registered")
    elif lab <= 0: raise ValueError("Lab id must be positive")
    elif lab > len(leaderboard): raise LeaderboardLabError(username, lab)
    elif name not in leaderboard[lab - 1]: raise LeaderboardUserError(username, lab)
    else: return leaderboard[lab - 1][name]
