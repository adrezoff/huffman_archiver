class ProgressBar:
    def __init__(self, total=0, length=50):
        self.total = total
        self.length = length
        self.progress = 0

    def update(self, progress):
        self.progress += progress
        if self.total != 0:
            percent = float(self.progress) / self.total
        else:
            percent = 1
        arrow = '#' * int(self.length * percent)
        spaces = ' ' * (self.length - len(arrow))
        print('\r[{}{}] {:.2f}%'.format(arrow, spaces, percent * 100), end='', flush=True)

    def reset(self, total):
        self.total = total
        self.progress = 0
        self.update(0)
