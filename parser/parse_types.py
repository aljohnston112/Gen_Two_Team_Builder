import json
import typing
from collections import defaultdict

import cattr

from config import ROOT, TYPE_FILE


def parse_type_chart():
    with open(ROOT + "/gen2To5TypeChart", "r") as f:
        done = False
        defender = f.readline().split()
        super_eff = defaultdict(list)
        not_eff = defaultdict(list)
        no_eff = defaultdict(list)

        s = f.readline().replace("×", "").replace("½", "0.5").split()
        while not done:
            attacker = s[0]
            for i, mul in enumerate(s[1:]):
                m = float(mul)
                if m == 0.5:
                    not_eff[attacker].append(defender[i])
                if m == 0:
                    no_eff[attacker].append(defender[i])
                if m == 2:
                    super_eff[attacker].append(defender[i])
            s = f.readline()
            if s == "":
                done = True
            s = s.replace("×", "").replace("½", "0.5").split()
        with open(TYPE_FILE, "w") as fo:
            list_ = [no_eff, not_eff, super_eff]
            fo.write(json.dumps(cattr.unstructure(list_)))


# [no_eff, not_eff, super_eff]
def get_type_dict():
    with open(TYPE_FILE, "r") as fo:
        return cattr.structure(json.loads(fo.read()), typing.List[typing.DefaultDict[str, typing.List[str]]])

