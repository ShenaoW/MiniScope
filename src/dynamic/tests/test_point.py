from .context import pgc
from pgc.models.point import Point


def test_is_close_to():
    assert Point(753.0, 1325.5, 1).is_close_to(Point(753.0, 1325.5, 1)) == True