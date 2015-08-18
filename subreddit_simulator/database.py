import json
import os
import sys
from ConfigParser import SafeConfigParser

from sqlalchemy import create_engine, Text, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def build_db_conn_string(cfg):
    if cfg.get("database", "system").lower() == "sqlite":
        return "{system}:///{db}".format(**{
            "system": cfg.get("database", "system"),
            "db": cfg.get("database", "database"),
        })

    return "{system}://{username}:{password}@{host}/{db}".format(**{
        "system": cfg.get("database", "system"),
        "username": cfg.get("database", "username"),
        "password": cfg.get("database", "password"),
        "host": cfg.get("database", "host"),
        "db": cfg.get("database", "database"),
    })


class JSONSerialized(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)


cfg_file = SafeConfigParser()
path_to_cfg = os.path.dirname(__file__)
path_to_cfg = os.path.join(path_to_cfg, "subreddit_simulator.cfg")
cfg_file.read(path_to_cfg)

engine = create_engine(build_db_conn_string(cfg_file))

Base = declarative_base()
Session = sessionmaker(bind=engine)
db = Session()
