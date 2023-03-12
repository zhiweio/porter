#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import logging
import os
import re

import poyo

from porter.exceptions import ConfigDoesNotExistException, InvalidConfiguration

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "reader": "",
    "redis": {
        "host": "localhost",
        "port": 6379,
        "password": None,
        "key": "PORTER_TEST",
        "queue_key_prefix": "porter.queue.",
        "cache_key_prefix": "porter.cache.",
    },
    "mysqlproxy": {
        "host": "localhost",
        "port": 80,
        "db": None,
        "table": None,
        "pk": "id",
        "column": None,
        "sharding": 0,
        "appendices": list(),
        "append_db_info": False,
    },
    "mysql": {
        "host": "localhost",
        "port": 3306,
        "db": None,
        "user": "test",
        "password": "123456",
        "table": None,
        "pk": "id",
        "column": None,
        "appendices": list(),
        "append_db_info": False,
    },
    "file": {"path": None, "delimiter": ",", "header": True, "appendices": list()},
    "json": {"path": None, "appendices": list()},
    "mongo": {
        "host": "localhost",
        "port": 3306,
        "db": None,
        "user": "test",
        "password": "123456",
        "collection": None,
        "column": None,
        "appendices": list(),
    },
    "porter_dir": os.path.expanduser("~/.porter/"),
}


def _expand_path(path):
    """Expand both environment variables and user home in the given path."""
    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    return path


def merge_configs(default, overwrite):
    """Recursively update a dict with the key/value pair of another.

    Dict values that are dictionaries themselves will be updated, whilst
    preserving existing keys.
    """
    new_config = copy.deepcopy(default)

    for k, v in overwrite.items():
        # Make sure to preserve existing items in
        # nested dicts, for example `abbreviations`
        if isinstance(v, dict):
            new_config[k] = merge_configs(default[k], v)
        else:
            new_config[k] = v

    return new_config


def get_config(config_path):
    """Retrieve the config from the specified path, returning a config dict."""
    if not os.path.exists(config_path):
        raise ConfigDoesNotExistException(
            "Config file {} does not exist.".format(config_path)
        )

    logger.debug("config_path is %s", config_path)
    with open(config_path, encoding="utf-8") as file_handle:
        try:
            yaml_dict = poyo.parse_string(file_handle.read())
        except poyo.exceptions.PoyoException as e:
            raise InvalidConfiguration(
                "Unable to parse YAML file {}. Error: {}".format(config_path, e)
            )

    config_dict = merge_configs(DEFAULT_CONFIG, yaml_dict)
    convert_delimiter(config_dict)
    # check appendices format
    reader_type = config_dict["reader"]
    for a in config_dict[reader_type]["appendices"]:
        logger.debug(f"check appendices: {a}")
        if reader_type == "file" and config_dict[reader_type]["header"] is False:
            break
        if not re.match(r"^.+:.+$", a):
            raise InvalidConfiguration(
                f"format error appendices: {a}, should be ^\w+:\w+$"
            )

    raw_porter_dir = config_dict["porter_dir"]
    config_dict["porter_dir"] = _expand_path(raw_porter_dir)

    return config_dict


def convert_delimiter(config):
    # special processing Tabs due to YAML forbid Tabs
    if config["reader"] == "file":
        if config["file"]["delimiter"] == "\\t":
            config["file"]["delimiter"] = "\t"
