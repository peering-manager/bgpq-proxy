import json
import logging
import re
from socket import AF_INET, AF_INET6

from flask import current_app

logger = logging.getLogger(__name__)

PATTERN_AS = re.compile(r"AS[0-9]+")
# https://www.ripe.net/manage-ips-and-asns/db/support/documentation/ripe-database-documentation/rpsl-object-types/4-2-descriptions-of-primary-objects/4-2-7-description-of-the-as-set-object
PATTERN_AS_SET = re.compile(r"AS-\w+")


class Cache(object):
    def __init__(self, redis, bgpq):
        self._redis = redis
        self._bgpq = bgpq
        self._ttl = current_app.config["CACHE_TIMEOUT"]

    @staticmethod
    def _format_asn(asn):
        try:
            int(asn)
            asn = f"AS{asn}"
        except ValueError:
            pass

        return asn.upper()

    @staticmethod
    def _format_as_set(as_set):
        # AS-SET must start with AS-
        if not as_set.startswith("AS-"):
            as_set = f"AS-{as_set}"

        return as_set.upper()

    @staticmethod
    def _validate_as_set(as_set):
        if as_set.count(":") == 0:
            if PATTERN_AS_SET.match(as_set) is None:
                raise ValueError(f"Invalid AS-SET: {as_set}")
        else:
            for part in as_set.split(":"):
                if (
                    PATTERN_AS_SET.match(part) is None
                    and PATTERN_AS.match(part) is None
                ):
                    raise ValueError(
                        f"Invalid hierarchical AS-SET: {as_set} (part {part})"
                    )

    def _fetch_from_cache(self, key, invalidate=False):
        """
        Return a value, given a key, from the redis cache.
        """
        ttl = self._redis.ttl(key)

        if ttl == -2:
            return None
        if ttl == -1:
            logger.warning(f"key {key} has no TTL, and is possibly stale")

        if invalidate:
            self._redis.delete(key)
            return None

        return json.loads(self._redis.get(key).decode())

    def _save_to_cache(self, key, value, ttl):
        """
        Saves a key/value pair in the redis cache with a TTL.
        """
        self._redis.set(key, json.dumps(value), ex=ttl)

    def get_asns(self):
        """
        Generator returning currently cached ASNs. If both IPv4 and IPv6 are in the
        cache for the ASN, it will still appear only once in the list.
        """
        seen_asns = []

        self._redis.scan_iter()

        for key in self._redis.scan_iter(match="asn:*", count=10):
            try:
                asn = key.decode().split(":")[1]
                if asn not in seen_asns:
                    yield asn
                    seen_asns.append(asn)
            except IndexError:
                logger.warning(f"could not extract ASN from key: [{key}]")

    def get_asn(self, asn, af=AF_INET, invalidate=False, no_cache=False):
        """
        Fetches the prefixes for an ASN, from the cache if it's in it.
        """
        asn = self._format_asn(asn)
        if not PATTERN_AS.match(asn):
            raise ValueError(f"Invalid AS: {asn}")

        key = f"asn:{asn}"
        if af == AF_INET:
            key += ":ipv4"
        elif af == AF_INET6:
            key += ":ipv6"
        else:
            raise ValueError(f"Unsupported address family: {af}")

        value = self._fetch_from_cache(key, invalidate=invalidate)
        if not value or no_cache:
            value = self._bgpq.get_asn(asn, address_family=af)

        if not no_cache:
            self._save_to_cache(key, value, self._ttl)

        return value

    def get_as_sets(self):
        """
        Generator returning currently cached AS-SETs. If both IPv4 and IPv6 are in the
        cache for the AS-SET, it will still appear only once in the list.
        """
        seen_as_sets = []

        self._redis.scan_iter()

        for key in self._redis.scan_iter(match="as_set:*", count=10):
            try:
                as_set = ":".join(key.decode().split(":")[1:-1])
                if as_set not in seen_as_sets:
                    yield as_set
                    seen_as_sets.append(as_set)
            except IndexError:
                logger.warning(f"could not extract AS-SET from key: [{key}]")

    def get_as_set(self, as_set, af=AF_INET, depth=0, invalidate=False, no_cache=False):
        """
        Fetches the prefixes for an AS-SET, from the cache if it's in it.
        """
        as_set = self._format_as_set(as_set)
        self._validate_as_set(as_set)

        key = f"as_set:{as_set}"
        if af == AF_INET:
            key += ":ipv4"
        elif af == AF_INET6:
            key += ":ipv6"
        else:
            raise ValueError(f"Unsupported address family: {af}")

        try:
            depth = int(depth)
        except ValueError:
            raise ValueError("depth must be an integer")

        if depth > 0:
            key += f":{depth}"

        value = self._fetch_from_cache(key, invalidate=invalidate)
        if not value or no_cache:
            value = self._bgpq.get_as_set(as_set, address_family=af, depth=depth)

        if not no_cache:
            self._save_to_cache(key, value, self._ttl)

        return value
