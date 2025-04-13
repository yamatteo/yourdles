import os
from pathlib import Path
from typing import Any, Optional

import dotenv
import dynamic_yaml
from dynamic_yaml.yaml_wrappers import YamlDict


class BunchDict(dict):
    def __init__(self, **kw):
        kw = {
            key: BunchDict(**value) if isinstance(value, YamlDict) else value
            for key, value in kw.items()
        }
        dict.__init__(self, kw)
        self.__dict__.update(kw)

    def __getattr__(self, name: str):
        # assume self.name give AttributeError
        return BunchDict()


def load(path: Optional[Path | str] = None, /):
    global dynamic_conf, conf

    envs = dotenv.dotenv_values(dotenv_path=os.getenv("ENVFILE"))
    if path is None:
        path = Path(envs.get("SETTINGS_FILE", "./settings.yaml"))

    if not path.exists():
        raise RuntimeError(f"Settings file was not found at {path.absolute()}")
    with open(path) as fileobj:
        dynamic_conf = dynamic_yaml.load(fileobj)
        if not hasattr(dynamic_conf, "envs"):
            dynamic_conf.envs = dict()
        for key, value in envs.items():
            setattr(dynamic_conf.envs, key, value)
        conf = BunchDict(**dynamic_conf)


def set(name: str, value: Any):
    global dynamic_conf, conf
    *parts, last = name.split(".")
    obj = dynamic_conf
    for key in parts:
        obj = getattr(obj, key)
    setattr(obj, last, value)

    conf = BunchDict(**dynamic_conf)
    return conf


dynamic_conf = YamlDict()
conf = BunchDict()
