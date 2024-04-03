def progress_bar(progress, total, length=50):
    progress = min(progress, total)
    percent = float(progress) / total
    arrow = '#' * int(length * percent)
    spaces = ' ' * (length - len(arrow))
    print('\r[{}{}] {:.2f}%'.format(arrow, spaces, percent * 100), end='', flush=True)
