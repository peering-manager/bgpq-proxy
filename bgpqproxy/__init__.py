import os

from flask import Flask
from flask_restful import Api

from bgpqproxy.api import BGPqAS, BGPqASList, BGPqASSet, BGPqASSetList


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(
        f'bgpqproxy.config.{os.environ.get("FLASK_ENV", "production")}.BaseConfig'
    )

    api = Api(app)
    api.add_resource(BGPqASList, "/bgpq/asn/")
    api.add_resource(BGPqAS, "/bgpq/asn/<string:asn>")
    api.add_resource(BGPqASSetList, "/bgpq/as-set/")
    api.add_resource(BGPqASSet, "/bgpq/as-set/<string:as_set>")

    return app
