class APIError(Exception):
    pass


class TooManyRequestError(APIError):
    pass


class ServerError(APIError):
    pass


class SirenError(APIError):
    pass
