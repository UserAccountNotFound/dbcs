class ServiceError(Exception):
    pass


class EmailAlreadyExistsError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class InvalidRefreshTokenError(ServiceError):
    pass


class CardNotFoundError(ServiceError):
    pass


class TemplateNotFoundError(ServiceError):
    pass


class SlugGenerationError(ServiceError):
    pass

class InvalidFileError(ServiceError):
    pass


class FileTooLargeError(ServiceError):
    pass


class UnsupportedFileTypeError(ServiceError):
    pass


class FileNotFoundError(ServiceError):
    pass


class TemplateError(ServiceError):
    pass