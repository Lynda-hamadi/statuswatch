import ipaddress
import os
import socket
from urllib.parse import urlparse


class UnsafeTarget(ValueError):
    """Adresse refusée parce qu'elle pointe vers un réseau non public."""


def assert_public_url(url: str) -> None:
    # Lu à chaque appel (et non à l'import) pour pouvoir être modifié dans les tests
    if os.getenv("ALLOW_PRIVATE_TARGETS", "false").lower() == "true":
        return

    host = urlparse(url).hostname
    if not host:
        raise UnsafeTarget("Adresse invalide")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # Le nom ne se résout pas : il n'y a rien à atteindre, la vérification notera la panne
        return

    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        # Une adresse IPv6 peut cacher une adresse IPv4 interne (::ffff:127.0.0.1)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global:
            raise UnsafeTarget(f"{host} pointe vers une adresse non publique ({ip})")