class Point:
    def __init__(self, x, y, judge) -> None:
        self.x     = x
        self.y     = y
        self.judge = judge
    
    def is_close_to(self, other):
        return abs(self.x - other.x) < 2 and abs(self.y - other.y) < 2