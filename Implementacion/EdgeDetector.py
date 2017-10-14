class EdgeDetector:
    """Detects False to True transitions on an external signal."""

    def __init__(self, reader, action):
        self.reader = reader
        self.action = action
        self.last_value = reader()    # initialise value

    def test(self):
        new_value = self.reader()
        if new_value and not self.last_value:
            self.action()
        self.last_value = new_value

if __name__ == '__main__':                 # simple self-test
    vlist = [False, False, False, True, True, False, True, True, False, False, False, True]
    vgen = (v for v in vlist)              # generator for value sequence

    def test_reader():                     # generate test sequence
        value = next(vgen)
        print("Read:", value)
        return value

    def printer():
        print("Edge transition detected")

    test_subject = EdgeDetector(test_reader, printer)
    for i in range(len(vlist)-1):
        test_subject.test()