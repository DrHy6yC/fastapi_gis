class AppError(Exception):
    detail = "Неожиданная ошибка"

    def __init__(self, *args):
        super().__init__(self.detail, *args)


class ObjectNotFoundError(AppError):
    detail = "Объект не найден"