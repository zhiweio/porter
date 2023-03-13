#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import json
import os
import sys

import click
from click.exceptions import MissingParameter

from porter import __version__
from porter.config import get_config
from porter.log import configure_logger
from porter.reader import (
    FileReader,
    JsonReader,
    MongoReader,
    MySQLReader,
)

REDAERS = {
    "mysql": MySQLReader,
    "json": JsonReader,
    "file": FileReader,
    "csv": FileReader,
    "mongo": MongoReader,
}


def version_msg():
    """Return the Porter version, location and Python powering it."""
    python_version = sys.version[:3]
    location = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return f"Porter %(version)s from {location} (Python {python_version})"


def new_task_template(task_type):
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    templates = {
        "mysqlproxy": "mysqlproxy.yaml",
        "mysql": "mysql.yaml",
        "json": "json.yaml",
        "file": "file.yaml",
        "csv": "csv.yaml",
        "mongo": "mongo.yaml",
    }
    for k, v in templates.items():
        templates[k] = os.path.join(template_dir, v)
    with codecs.open(templates[task_type], encoding="utf8") as f:
        return f.read()


def process_configure(config_file):
    config = get_config(config_file)
    if config["reader"] not in {"file", "csv", "json", "mysql", "mysqlproxy", "mongo"}:
        click.echo(f"config error, please check {config_file}")
        sys.exit(-1)

    return config["reader"], config[config["reader"]], config["redis"]


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(__version__, "-V", "--version", message=version_msg())
@click.argument("todo", type=click.Choice(["sync", "monitor", "clear", "new"]))
@click.option(
    "-f",
    "--config-file",
    type=click.Path(exists=True, readable=True),
    help="Task config file",
)
@click.option(
    "-l",
    "--limit",
    type=int,
    default=1000,
    show_default=True,
    help="Limit of each reading from data source",
)
@click.option(
    "--limit-scale",
    type=int,
    default=3,
    show_default=True,
    help="The maximum lengeth of redis queue is (limit * scale)",
)
@click.option(
    "--blocking/--no-blocking",
    " /-B",
    default=True,
    show_default=True,
    help="Enable blocking mode",
)
@click.option(
    "-t",
    "--time-sleep",
    type=int,
    default=10,
    show_default=True,
    help="Time to wait when up to the maximum limit of queue",
)
@click.option(
    "-C",
    "--clean-type",
    type=click.Choice(["status", "queue", "all"]),
    show_default=True,
    help="Type of redis cache ",
)
@click.option(
    "-T",
    "--task-type",
    type=click.Choice(["mysql", "mongo", "json", "file", "csv"]),
    show_default=True,
    help="Type of task template ",
)
@click.option(
    "-o", "--output-task-file", type=click.Path(), help="Save task template into file"
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Print debug information"
)
@click.option(
    "--debug-file",
    type=click.Path(),
    default=None,
    help="File to be used as a stream for DEBUG logging",
)
@click.pass_context
def main(
    ctx,
    todo,
    config_file,
    limit,
    limit_scale,
    blocking,
    time_sleep,
    clean_type,
    task_type,
    output_task_file,
    verbose,
    debug_file,
):
    """A command line tool for extracting data and load into Redis."""
    # set log
    configure_logger(stream_level="DEBUG" if verbose else "INFO", debug_file=debug_file)
    # task template
    if todo == "new" and task_type:
        task_template = new_task_template(task_type)
        if output_task_file:
            with codecs.open(output_task_file, "w", encoding="utf8") as f:
                f.write(task_template)
        else:
            click.echo(task_template)
        sys.exit(0)

    # option `config-file` required if [sync|monitor|clear]
    if not config_file:
        raise MissingParameter(
            ctx=ctx, param_type="option", param_hint="'-f' / '--config-file'"
        )

    reader_type, reader_config, redis_config = process_configure(config_file)
    if reader_type == "mysqlproxy":
        sharding = reader_config["sharding"]
        if sharding == 0:
            ReaderKlass = MySQLProxyReader
        elif sharding == 1 or sharding == 2:
            ReaderKlass = MultiMySQLProxyReader
        else:
            click.echo("Error config, sharding flag must be [0, 1, 2]")
            sys.exit(-1)
    else:
        ReaderKlass = REDAERS[reader_type]

    reader = ReaderKlass(
        reader_config,
        redis_config,
        limit=limit,
        block=blocking,
        scale=limit_scale,
        sleep=time_sleep,
    )

    # start sync task
    if todo == "sync":
        reader.sync()

    # monitor task status
    elif todo == "monitor":
        print(json.dumps(reader.status(), ensure_ascii=False, indent=4))

    # clear task cache
    elif todo == "clear" and clean_type:
        reader.clear(clean_type)


if __name__ == "__main__":
    main()
