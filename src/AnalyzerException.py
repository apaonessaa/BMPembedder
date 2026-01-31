class ValueNotInExcludeEnd(Exception):
    def __init__(self, message, x, start, end):
        super().__init__(self.message)
        self.x = x
        self.start = start
        self.end = end

    def __str__(self):
        return f"ValueNotInExcludeEnd@{self.message}: {self.x} not in [{self.start},{self.end})"

