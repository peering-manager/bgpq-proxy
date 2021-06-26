import os

from flask import Flask
from flask_restful import Api

from bgpqproxy.utils.bgpq import BGPqAS, BGPqASSet


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(
        f'bgpqproxy.config.{os.environ.get("FLASK_ENV", "production")}.BaseConfig'
    )

    api = Api(app)
    api.add_resource(BGPqAS, "/bgpq/as/<string:asn>")
    api.add_resource(BGPqASSet, "/bgpq/as-set/<string:as_set>")

    return app
