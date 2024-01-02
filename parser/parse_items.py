import json
import typing

import cattr

from config import ROOT, ITEM_FILE


def parse_items():
    with open(ROOT + "/gen2HoldItems", "r") as f:
        items = {}
        done = False
        while not done:
            s = f.readline()
            if s != "":
                s = s.split("\t")
                item = s[0].strip()
                d = s[1].strip()
                items[item] = d
            else:
                done = True
        with open(ITEM_FILE, "w") as fo:
            fo.write(json.dumps(cattr.unstructure(items)))


def get_items():
    with open(ITEM_FILE, "r") as fo:
        return cattr.structure(json.loads(fo.read()), typing.Dict[str, str])

