import ipaddress
import re

from sqlalchemy import func, or_

from app.models import Cluster, Host, HostClusterRelation


def split_search_terms(keyword: str) -> list[str]:
    """Accept a pasted list of hostnames or IPs, without repeating terms."""
    return list(dict.fromkeys(term for term in re.split(r"[,，;；\s]+", keyword.strip()) if term))


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def host_keyword_filter(keyword: str):
    terms = split_search_terms(keyword)
    if not terms:
        return None
    if len(terms) > 100:
        raise ValueError("一次最多搜索 100 个关键词")

    matches = []
    for term in terms:
        try:
            ipaddress.ip_address(term)
        except ValueError:
            # Escape LIKE wildcards so pasted text is matched literally.
            escaped = escape_like(term)
            pattern = f"%{escaped}%"
            matches.append(or_(
                Host.hostname.ilike(pattern, escape="\\"),
                Host.private_ip.ilike(pattern, escape="\\"),
                Host.public_ip.ilike(pattern, escape="\\"),
                Host.open_ports.ilike(pattern, escape="\\"),
                Host.os.ilike(pattern, escape="\\"),
                Host.notes.ilike(pattern, escape="\\"),
                Host.cluster_relations.any(HostClusterRelation.cluster.has(or_(
                    Cluster.name.ilike(pattern, escape="\\"),
                    Cluster.cluster_type.ilike(pattern, escape="\\"),
                    Cluster.port.ilike(pattern, escape="\\"),
                ))),
            ))
        else:
            public_ips = func.replace(func.replace(Host.public_ip, " ", ""), "，", ",")
            escaped = escape_like(term)
            matches.append(or_(
                Host.private_ip == term,
                public_ips == term,
                public_ips.like(f"{escaped},%", escape="\\"),
                public_ips.like(f"%,{escaped},%", escape="\\"),
                public_ips.like(f"%,{escaped}", escape="\\"),
            ))
    return or_(*matches)
