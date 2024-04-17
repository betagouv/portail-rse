SERVER_ERROR = "Le service est actuellement indisponible. Merci de réessayer plus tard."
SIREN_NOT_FOUND_ERROR = (
    "L'entreprise n'a pas été trouvée. Vérifiez que le SIREN est correct."
)
TOO_MANY_REQUESTS_ERROR = "Le service est temporairement surchargé. Merci de réessayer."

API_ERROR_SENTRY_MESSAGE = "Erreur API {}"
INVALID_REQUEST_SENTRY_MESSAGE = "Requête invalide sur l'API {}"
TOO_MANY_REQUESTS_SENTRY_MESSAGE = "Trop de requêtes sur l'API {}"


class APIError(Exception):
    pass


class TooManyRequestError(APIError):
    pass


class ServerError(APIError):
    pass


class SirenError(APIError):
    pass
