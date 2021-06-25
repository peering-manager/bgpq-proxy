import os

from flask import Flask
from flask_restful import Api

from utils.bgpq import BGPqAS, BGPqASSet

app = Flask(__name__)
app.config.from_object(f'config.{os.environ.get("FLASK_ENV", "production")}.BaseConfig')

api = Api(app)
api.add_resource(BGPqAS, "/bgpq/as/<string:asn>")
api.add_resource(BGPqASSet, "/bgpq/as-set/<string:as_set>")

if __name__ == "__main__":
    """
    This entrypoint should only be used for testing purposes.
    """
    app.run(debug=True)
