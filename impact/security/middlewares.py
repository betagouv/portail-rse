import ipaddress

from django.conf import settings
from django.http import HttpResponseNotFound

from logs import event_logger as logger


class IPBlocklistMiddleware:
    """
    Bloque les requêtes provenant d'adresses IP ou de subnets listés dans BLOCKED_IP_SUBNETS.
    Supporte aussi bien les IP individuelles que les notations CIDR (ex: 192.168.1.0/24).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Parse la liste des subnets bloqués au démarrage
        self.blocked_networks = []
        blocked_subnets = settings.BLOCKED_IP_SUBNETS
        self.logme = settings.BLOCKED_IP_SUBNETS_LOG

        # A l'initialisation uniquement : inutile de répéter l'extraction
        if blocked_subnets:
            for subnet in blocked_subnets.split(","):
                subnet = subnet.strip()
                if subnet:
                    try:
                        self.blocked_networks.append(
                            ipaddress.ip_network(subnet, strict=False)
                        )
                    except ValueError as ex:
                        # Log l'erreur mais ne plante pas l'application
                        if self.logme:
                            logger.error("security:ip_filter", {"cause": ex})

    def __call__(self, request):
        # Récupère l'IP réelle (en tenant compte des proxies Scalingo)
        # Scalingo transmet l'IP source via X-Forwarded-For et X-Real-Ip
        ip = None

        # Priorité 1 : X-Forwarded-For (peut contenir plusieurs IPs séparées par des virgules)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Prendre la première IP de la liste (IP source originale)
            ip = x_forwarded_for.split(",")[0].strip()

        # Priorité 2 : X-Real-IP (fallback si X-Forwarded-For absent)
        if not ip:
            ip = request.META.get("HTTP_X_REAL_IP")

        # Priorité 3 : REMOTE_ADDR (dernière option, sera une IP interne 10.x)
        if not ip:
            ip = request.META.get("REMOTE_ADDR")

        # Vérifie si l'IP est dans un subnet bloqué
        if ip and self.blocked_networks:
            try:
                ip_address = ipaddress.ip_address(ip)
                for network in self.blocked_networks:
                    if ip_address in network:
                        if self.logme:
                            logger.warning(
                                "security:ip_blocked",
                                {
                                    "ip": str(ip_address),
                                    "subnet": str(network),
                                    "path": request.path,
                                    "method": request.method,
                                },
                            )
                        # 404 mieux que 403
                        return HttpResponseNotFound("Not found")
            except ValueError as ex:
                if self.logme:
                    # IP invalide, logger pour diagnostic
                    logger.warning(
                        "security:invalid_ip",
                        {
                            "ip": ip,
                            "x_forwarded_for": request.META.get("HTTP_X_FORWARDED_FOR"),
                            "x_real_ip": request.META.get("HTTP_X_REAL_IP"),
                            "remote_addr": request.META.get("REMOTE_ADDR"),
                            "error": str(ex),
                        },
                    )

        return self.get_response(request)
