import json
import subprocess
from socket import AF_INET, AF_INET6

from bgpqproxy.redis import redis_client
from flask import current_app
from flask_restful import Resource, reqparse


class ApiResource(Resource):
    def get_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument("depth", type=int, default=0)
        parser.add_argument("invalidate", type=bool, default=False)
        parser.add_argument("no_cache", type=bool, default=False)

        return parser.parse_args()


class BGPqAS(ApiResource):
    def get(self, asn):
        try:
            int(asn)
            asn = f"AS{asn}"
        except ValueError:
            pass

        args = self.get_args()
        bgpq = BGPqRunner()

        try:
            return {
                "ipv4": bgpq.get_prefixes(
                    asn,
                    AF_INET,
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
                "ipv6": bgpq.get_prefixes(
                    asn,
                    AF_INET6,
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
            }
        except ValueError as e:
            return {"error": str(e)}, 400


class BGPqASSet(ApiResource):
    def get(self, as_set):
        args = self.get_args()
        bgpq = BGPqRunner()

        try:
            return {
                "ipv4": bgpq.get_prefixes(
                    as_set,
                    AF_INET,
                    depth=args["depth"],
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
                "ipv6": bgpq.get_prefixes(
                    as_set,
                    AF_INET6,
                    depth=args["depth"],
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
            }
        except ValueError as e:
            return {"error": str(e)}, 400


class BGPqRunner(object):
    def __init__(self):
        self._path = current_app.config["BGPQ_PATH"]

    def get_prefixes(
        self,
        irr_object,
        address_family=AF_INET,
        depth=0,
        invalidate=False,
        no_cache=False,
    ):
        """
        Call a subprocess to expand the given AS-SET for an IP version.
        """
        if address_family not in (AF_INET, AF_INET6):
            raise ValueError(f"Unsupported IP address family: {address_family}")

        cache_key = f"{irr_object}_{address_family}"
        cached_value = redis_client().get(cache_key)

        # Don't return a cached result if user asked set `no_cache`
        if not no_cache and cached_value:
            if invalidate:
                redis_client().delete(cache_key)
            else:
                # Return a cached value if available
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
                error_log += f", stderr: {err.decode()}"
            raise ValueError(error_log)

        # Parse stdout as JSON and cache the result
        prefixes = json.loads(out.decode())["prefixes"]
        if not invalidate and not no_cache:
            # Cache result only if `invalidate` and `no_cache` are not set
            redis_client().set(cache_key, json.dumps(prefixes), ex=86400)

        return prefixes
