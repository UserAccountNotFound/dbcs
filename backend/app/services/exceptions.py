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