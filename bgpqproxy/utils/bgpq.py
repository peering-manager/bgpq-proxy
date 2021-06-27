import json
import subprocess
from socket import AF_INET, AF_INET6

from flask import current_app


class BGPqRunner(object):
    def __init__(self):
        self._path = current_app.config["BGPQ_PATH"]

    def _get_prefixes(self, irr_object, address_family=AF_INET, depth=0):
        """
        Calls a subprocess to expand the given AS or AS-SET.
        """
        if address_family not in (AF_INET, AF_INET6):
            raise ValueError(f"Unsupported IP address family: {address_family}")

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

        # Parse stdout as JSON
        return json.loads(out.decode())["prefixes"]

    def get_asn(self, asn, address_family=AF_INET):
        return self._get_prefixes(asn, address_family=address_family)

    def get_as_set(self, as_set, address_family=AF_INET, depth=0):
        return self._get_prefixes(as_set, address_family=address_family, depth=depth)
