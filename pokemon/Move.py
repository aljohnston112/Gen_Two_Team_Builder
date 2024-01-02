import attr


@attr.s
class Move:

    name = attr.ib()
    type_ = attr.ib()
    split = attr.ib()
