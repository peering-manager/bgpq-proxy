import json
import subprocess
from socket import AF_INET, AF_INET6

from bgpqproxy.redis import redis_client
from flask import current_app
from flask_restful import Resource, reqparse


class BGPqAS(Resource):
    def get(self, asn):
        try:
            int(asn)
            asn = f"AS{asn}"
        except ValueError:
            pass

        bgpq = BGPqRunner()

        return {
            "ipv4": bgpq.get_prefixes(asn, AF_INET),
            "ipv6": bgpq.get_prefixes(asn, AF_INET6),
        }


class BGPqASSet(Resource):
    def get(self, as_set):
        # Parse depth parameter if given, assume 0 otherwise
        parser = reqparse.RequestParser()
        parser.add_argument("depth", type=int, default=0)
        args = parser.parse_args()

        bgpq = BGPqRunner()

        return {
            "ipv4": bgpq.get_prefixes(as_set, AF_INET, depth=args["depth"]),
            "ipv6": bgpq.get_prefixes(as_set, AF_INET6, depth=args["depth"]),
        }


class BGPqRunner(object):
    def __init__(self):
        self._path = current_app.config["BGPQ_PATH"]

    def get_prefixes(self, irr_object, address_family=AF_INET, depth=0):
        """
        Call a subprocess to expand the given AS-SET for an IP version.
        """
        if address_family not in (AF_INET, AF_INET6):
            raise ValueError(f"Unsupported IP address family: {address_family}")

        cache_key = f"{irr_object}_{address_family}"
        cached_value = redis_client().get(cache_key)

        # Return a cached value if available
        if cached_value:
            return json.loads(cached_value)

        # Build bgpq(3|4) arguments to get a JSON result
        command = [
            self._path,
            "-4" if address_family == AF_INET else "-6",
            "-A",
            "-j",
            "-l",
            "prefixes",
        ]

        # Avoid going to deep if demanded
        if depth > 0:
            command.extend(["-L", str(depth)])

        # And finally give the IRR object
        command.append(irr_object)

        # Execute the process and catch stdout/stderr
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.communicate()

        # Find out if an error occured
        if process.returncode != 0:
            error_log = f"{self._path} exit code is {process.returncode}"
            if err and err.strip():
                error_log += f", stderr: {err}"
            raise ValueError(error_log)

        # Parse stdout as JSON and cache the result
        prefixes = json.loads(out.decode())["prefixes"]
        redis_client().set(cache_key, json.dumps(prefixes), ex=86400)

        return prefixes
