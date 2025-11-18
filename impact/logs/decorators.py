from functools import wraps

from logs import event_logger as logger


def log_path(msg: str):
    """
    Décorateur pour logger les parcours utilisateur.

    Args:
        msg: Message à logger

    Utilisation:
        @log_path("page:mon_parcours")
        def ma_vue(request, ...):
            ...

    Loggue les informations suivantes (si disponibles):
        - idUtilisateur: PK de l'utilisateur connecté
        - siren: SIREN de l'entreprise (depuis la session)
        - session: Identifiant de session
    """

    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            payload = {}

            # Récupérer l'ID utilisateur si connecté
            if hasattr(request, "user") and request.user.is_authenticated:
                payload |= {"idUtilisateur": request.user.pk}

            # Récupérer le SIREN depuis la session
            if hasattr(request, "session") and "entreprise" in request.session:
                payload |= {"siren": request.session["entreprise"]}

            # Récupérer l'identifiant de session
            if hasattr(request, "session") and request.session.session_key:
                payload |= {"session": request.session.session_key}

            # Logger le parcours utilisateur (si il ya des données)
            if payload:
                logger.info(msg, payload)

            # Exécuter la vue
            return function(request, *args, **kwargs)

        return wrap

    return decorator
