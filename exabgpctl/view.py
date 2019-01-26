# -*- coding: utf-8 -*-
"""
exabgpctl.view
~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, print_function

# standard
import sys

# third
import click

# local
from exabgpctl.controller import (
    config_load,
    get_version,
    disable_process,
    enable_process,
    get_process,
    list_disabled_processes,
    list_enabled_processes,
    list_processes,
    state_process,
    status_processes,
    get_neighbor,
    list_neighbors,
    status_neighbors,
    print_json,
    print_yaml,
    print_flat,
    ExabgpCTLError,
)

# Context


def create_context(output="json", debug=False):
    """Create a context for CLI - used for autocomplete because Click doesn't
    support it.

    See https://github.com/pallets/click/issues/942
    """
    obj = {"cfg": config_load(), "debug": debug}
    if output == "yaml":
        obj["output"] = print_yaml
    elif output == "flat":
        obj["output"] = print_flat
    else:
        obj["output"] = print_json
    return obj


# AutoComplete


def _ac_output(*_, **kwargs):
    """Autocomplete output"""
    outputs = ["flat", "json", "yaml"]
    if kwargs["incomplete"] is None:
        return outputs
    return [
        output.lower()
        for output in outputs
        if output.lower().startswith(kwargs["incomplete"].lower())
    ]


def _ac_list_processes(*_, **kwargs):
    """Autocomplete process names"""
    context = create_context()
    return [
        process.lower()
        for process in list_processes(context["cfg"])
        if process.lower().startswith(kwargs["incomplete"].lower())
    ]


def _ac_list_processes_enable(*_, **kwargs):
    """Autocomplete enabled process names"""
    context = create_context()
    return [
        process.lower()
        for process in list_disabled_processes(context["cfg"])
        if process.lower().startswith(kwargs["incomplete"].lower())
    ]


def _ac_list_processes_disable(*_, **kwargs):
    """Autocomplete disbled process names"""
    context = create_context()
    return [
        process.lower()
        for process in list_enabled_processes(context["cfg"])
        if process.lower().startswith(kwargs["incomplete"].lower())
    ]


def _ac_list_neighbors(*_, **kwargs):
    """Autocomplete neighbours names"""
    context = create_context()
    return [
        neighbor.lower()
        for neighbor in list_neighbors(context["cfg"])
        if neighbor.lower().startswith(kwargs["incomplete"].lower())
    ]


def _ac_list_key_version(*_, **kwargs):
    """Autocomplete version keys"""
    return [
        key.lower()
        for key in get_version().keys()
        if key.lower().startswith(kwargs["incomplete"].lower())
    ]


OPTS = {
    "output": {
        "args": ["--output", "-o"],
        "kwargs": {
            "help": "Output format.",
            "default": "json",
            "required": False,
            "type": click.Choice(_ac_output(incomplete=None)),
            "autocompletion": _ac_output,
        },
    },
    "debug": {
        "args": ["--debug", "-d"],
        "kwargs": {
            "help": "Enable debug.",
            "default": False,
            "required": False,
            "is_flag": True,
        },
    },
    "list_processes": {
        "args": ["--disable", "-d"],
        "kwargs": {
            "help": "Filter only disabled processes.",
            "required": False,
            "default": False,
            "is_flag": bool,
        },
    },
    "process": {
        "kwargs": {
            "required": True,
            "type": click.STRING,
            "autocompletion": _ac_list_processes,
        }
    },
    "process_disable": {
        "kwargs": {
            "required": True,
            "type": click.STRING,
            "autocompletion": _ac_list_processes_disable,
        }
    },
    "process_enable": {
        "kwargs": {
            "required": True,
            "type": click.STRING,
            "autocompletion": _ac_list_processes_enable,
        }
    },
    "neighbor": {
        "kwargs": {
            "required": True,
            "type": click.STRING,
            "autocompletion": _ac_list_neighbors,
        }
    },
    "version_key": {
        "kwargs": {
            "required": False,
            "default": None,
            "type": click.STRING,
            "autocompletion": _ac_list_key_version,
        }
    },
}

# CLI


@click.group()
@click.pass_context
@click.option(*OPTS["output"]["args"], **OPTS["output"]["kwargs"])
@click.option(*OPTS["debug"]["args"], **OPTS["debug"]["kwargs"])
def cli(ctx, output, debug):
    """ExaBGP admin CLI for managing processes."""
    ctx.ensure_object(dict)
    ctx.obj = create_context(output, debug)


@cli.command(name="dump")
@click.pass_context
def dump(ctx):
    """Dump configuration into JSON, useful with jq."""
    ctx.obj["output"](ctx.obj["cfg"])


@cli.command(name="status")
@click.pass_context
def status(ctx):
    """Status configuration into JSON, useful with jq."""
    ctx.obj["output"](
        {
            "processes": status_processes(ctx.obj["cfg"]),
            "neighbors": status_neighbors(ctx.obj["cfg"]),
        }
    )


@cli.command(name="version")
@click.pass_context
@click.argument("key", **OPTS["version_key"]["kwargs"])
def version(ctx, key):
    """Get version"""
    ctx.obj["output"](get_version(key))


@cli.command(name="edit")
@click.pass_context
def edit(ctx):
    """Edit exabgp config, change EDITOR environment variable
    to change default editor."""
    click.edit(filename=ctx.obj["cfg"]["path"])


# Processes


@cli.group(name="process")
@click.pass_context
# pylint: disable=unused-argument
def process_g(ctx):
    """Manage process."""


@process_g.command(name="list")
@click.pass_context
@click.option(
    *OPTS["list_processes"]["args"], **OPTS["list_processes"]["kwargs"]
)
def process_list(ctx, disable):
    """List processes or disabled process."""
    func = list_processes
    if disable:
        func = list_disabled_processes

    ctx.obj["output"](sorted(func(ctx.obj["cfg"])))


@process_g.command(name="show")
@click.pass_context
@click.argument("process", **OPTS["process"]["kwargs"])
def process_show(ctx, process):
    """Show proces details"""
    ctx.obj["output"](get_process(ctx.obj["cfg"], process))


@process_g.command(name="enable")
@click.pass_context
@click.argument("process", **OPTS["process_enable"]["kwargs"])
def process_enable(ctx, process):
    """Enable process maintenance"""
    ctx.obj["output"](enable_process(ctx.obj["cfg"], process))


@process_g.command(name="disable")
@click.pass_context
@click.argument("process", **OPTS["process_disable"]["kwargs"])
def process_disable(ctx, process):
    """Disable process maintenance"""
    ctx.obj["output"](disable_process(ctx.obj["cfg"], process))


@process_g.command(name="state")
@click.pass_context
@click.argument("process", **OPTS["process"]["kwargs"])
def process_state(ctx, process):
    """Change process state"""
    ctx.obj["output"](state_process(ctx.obj["cfg"], process))


@process_g.command(name="status")
@click.pass_context
def process_status(ctx):
    """Status of all processs."""
    ctx.obj["output"](status_processes(ctx.obj["cfg"]))


# Neighbours


@cli.group(name="neighbor")
@click.pass_context
# pylint: disable=unused-argument
def neighbor_g(ctx):
    """Manage neighbor."""


@neighbor_g.command(name="show")
@click.pass_context
@click.argument("neighbor", **OPTS["neighbor"]["kwargs"])
def neighbor_show(ctx, neighbor):
    """Process details"""
    ctx.obj["output"](get_neighbor(ctx.obj["cfg"], neighbor))


@neighbor_g.command(name="list")
@click.pass_context
def neighbor_list(ctx):
    """List neighbors."""
    ctx.obj["output"](sorted(list_neighbors(ctx.obj["cfg"])))


@neighbor_g.command(name="status")
@click.pass_context
def neighbor_status(ctx):
    """status neighbors."""
    ctx.obj["output"](status_neighbors(ctx.obj["cfg"]))


def main():
    """main"""
    try:
        cli()  # pylint: disable=no-value-for-parameter
    # catch only exabgp errors
    except ExabgpCTLError as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
