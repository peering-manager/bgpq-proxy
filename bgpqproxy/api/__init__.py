from socket import AF_INET, AF_INET6

from bgpqproxy.redis import redis_client
from bgpqproxy.services import Cache
from bgpqproxy.utils.bgpq import BGPqRunner
from flask_restful import Resource, reqparse


class ApiResource(Resource):
    def get_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument("depth", type=int, default=0)
        parser.add_argument("invalidate", type=bool, default=False)
        parser.add_argument("no_cache", type=bool, default=False)

        return parser.parse_args()


class BGPqASList(ApiResource):
    def get(self):
        cache = Cache(redis_client(), BGPqRunner())
        return {"asn": list(cache.get_asns())}


class BGPqASSetList(Resource):
    def get(self):
        cache = Cache(redis_client(), BGPqRunner())
        return {"as_sets": list(cache.get_as_sets())}


class BGPqAS(ApiResource):
    def get(self, asn):
        cache = Cache(redis_client(), BGPqRunner())
        args = self.get_args()

        try:
            return {
                "ipv4": cache.get_asn(
                    asn,
                    af=AF_INET,
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
                "ipv6": cache.get_asn(
                    asn,
                    af=AF_INET6,
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
            }
        except ValueError as e:
            return {"error": str(e)}, 400


class BGPqASSet(ApiResource):
    def get(self, as_set):
        cache = Cache(redis_client(), BGPqRunner())
        args = self.get_args()

        try:
            return {
                "ipv4": cache.get_as_set(
                    as_set,
                    af=AF_INET,
                    depth=args["depth"],
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
                "ipv6": cache.get_as_set(
                    as_set,
                    af=AF_INET6,
                    depth=args["depth"],
                    invalidate=args["invalidate"],
                    no_cache=args["no_cache"],
                ),
            }
        except ValueError as e:
            return {"error": str(e)}, 400
