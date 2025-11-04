# This is a poorly formatted test file
def badly_formatted_function(x, y, z):
    result = x + y + z
    return result


class PoorlyFormattedClass:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def calculate(self):
        return self.a + self.b + self.c


# This line was too long and exceeded the 88 character limit
# that Black enforces by default for Python code formatting
if __name__ == "__main__":
    obj = PoorlyFormattedClass(1, 2, 3)
    print(obj.calculate())
