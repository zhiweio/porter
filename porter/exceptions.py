#!/usr/bin/env python
# -*- coding: utf-8 -*-


class PorterException(Exception):
    pass


class MysqlHttpApiError(PorterException):
    pass


class ConfigDoesNotExistException(PorterException):
    """
    Exception for missing config file.

    Raised when get_config() is passed a path to a config file, but no file
    is found at that path.
    """


class InvalidConfiguration(PorterException):
    """
    Exception for invalid configuration file.

    Raised if the global configuration file is not valid YAML or is
    badly constructed.
    """
