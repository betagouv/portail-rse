import ipaddress
import os

from django.http import HttpResponseForbidden

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
        blocked_subnets = os.environ.get("BLOCKED_IP_SUBNETS", "")

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
                        logger.error("security:ip_filter", {"cause": ex})

    def __call__(self, request):
        # Récupère l'IP réelle (en tenant compte des proxies)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        # Vérifie si l'IP est dans un subnet bloqué
        if ip and self.blocked_networks:
            try:
                ip_address = ipaddress.ip_address(ip)
                for network in self.blocked_networks:
                    if ip_address in network:
                        logger.warning("security:ip_filter", {"filtered": ip_address})
                        return HttpResponseForbidden("Access denied")
            except ValueError:
                # IP invalide, on laisse passer (ou on bloque selon votre politique)
                pass

        return self.get_response(request)
