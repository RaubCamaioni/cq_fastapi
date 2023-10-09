import cadquery as cq
from math import cos, sin, pi
import numpy as np
from typing import Tuple, List

def create_stand(
    mounts: List[Tuple[float, float]],
    angle: float = 60,
    screw_size: float = 2.4,
    edge_padding: float = 5,
    padding: float = 10,
    thickness: float = 3,
):
    """
    Simple mounting solution constructor.
    """

    angle = angle * pi / 180
    ss = screw_size / 2
    length = max([h for w, h in mounts])
    width = edge_padding * 2 + sum([w for w, h in mounts]) + padding * (len(mounts) - 1)

    # draw center line of edge projection, compensate for fillet
    lx = cos(angle) * (length + edge_padding)
    ly = sin(angle) * (length + edge_padding + thickness * 2)
    relative_points = np.array(
        [
            (0, 0),
            (lx, 0),
            (-lx, ly),
        ]
    )

    # thicken line to 2D face
    wire = cq.Workplane("XY").polyline(np.cumsum(relative_points, axis=0))
    face = wire.offset2D(thickness / 2, "arc")

    # extrude 2D face to 3D shape
    result = face.extrude(width)

    # transform mount dimentions to points
    def rect(cx: float, cy: float, w: float, h: float):
        w, h = w / 2, h / 2
        return [
            (h + cy, w + cx),
            (-h + cy, w + cx),
            (-h + cy, -w + cx),
            (h + cy, -w + cx),
        ]

    points = []
    cx = -edge_padding
    for w, h in mounts:
        cx -= w / 2
        points.extend(rect(cx, 0, w, h))
        cx -= w / 2 + padding

    # select face with largest surface area
    face = result.faces(selector=cq.selectors.AreaNthSelector(-1))

    # punch pi holes
    mount = (
        face.workplane(centerOption="CenterOfBoundBox")
        .center(0, 0 + width / 2)
        .pushPoints(points)
        .circle(ss)
        .extrude(-thickness, combine="cut")
    )

    return mount


if __name__ in ["__main__", "__cq_main__"]:
    import json
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str)
    parser.add_argument('--output', type=str)
    args = parser.parse_args()
    
    with open(args.config, 'r') as f:
        configs = json.load(f)

    # generate mount
    mount = create_stand(
        configs["mounts"],
        configs["angle"],
        configs["screw_size"],
        configs["edge_padding"],
        configs["padding"],
        configs["thickness"]
    )

    # export
    cq.exporters.export(mount, args.output)