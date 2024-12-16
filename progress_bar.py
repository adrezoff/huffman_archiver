class ProgressBar:
    """
    Представляет индикатор прогресса в командной строке.
    """

    def __init__(self, total: int = 0, length: int = 50) -> None:
        """
        Инициализирует объект класса ProgressBar.

        :param total: Общее количество для отслеживания прогресса.
        :param length: Длина индикатора прогресса.
        """
        self.total: int = total
        self.length: int = length
        self.progress: int = 0

    def update(self, progress: int) -> None:
        """
        Обновляет индикатор прогресса прибавляя заданное значение.

        :param progress: Прогресс для добавления.
        """
        self.progress += progress
        if self.total != 0:
            percent = float(self.progress) / self.total
        else:
            percent = 1
        self.drawer(percent)

    def update_with_point(self, pointer: int) -> None:
        """
        Обновляет индикатор прогресса до заданного значения.

        :param pointer: Значение указателя.
        """
        self.progress = pointer

        if self.total != 0:
            percent = float(pointer) / self.total
        else:
            percent = 1
        self.drawer(percent)

    def drawer(self, percent: float) -> None:
        """
        Отображает индикатор прогресса.

        :param percent: Процент выполнения операции.
        """
        arrow = '#' * int(self.length * percent)
        spaces = ' ' * (self.length - len(arrow))
        print('\r[{}{}] {:.2f}%'.format(arrow, spaces, percent * 100),
              end='', flush=True)

    def reset(self, total: int) -> None:
        """
        Сбрасывает индикатор прогресса и устанавливает новое значение цели.

        :param total: Новое общее количество для отслеживания прогресса.
        """
        self.total: int = total
        self.progress: int = 0
        self.update(0)
