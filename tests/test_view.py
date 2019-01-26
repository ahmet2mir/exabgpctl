# -*- coding: utf-8 -*-
# standard
import os
import json

# third
import yaml
import pytest
from mock import patch, MagicMock

# local
import exabgpctl

import click
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config():

    if exabgpctl._py6.PY2:
        exabgpctl_conf = os.path.abspath("examples/exabgp3.conf")
    else:
        exabgpctl_conf = os.path.abspath("examples/exabgp4.conf")

    return {"exabgp": "ctl", "path": os.path.abspath(exabgpctl_conf)}


def test_dump(runner, config):
    mocks = {}
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config
        with patch("exabgpctl.view.create_context") as ctx:
            for fmt in ["yaml", "json", "flat"]:
                mocks = {fmt: MagicMock(printer=fmt)}
                ctx.return_value = {
                    "debug": False,
                    "cfg": config,
                    "output": mocks[fmt],
                }
                result = runner.invoke(
                    exabgpctl.view.cli, ["--output", fmt, "dump"]
                )
                mocks[fmt].assert_called_with(config)


def test_create_context(config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        data = exabgpctl.view.create_context(output="yaml", debug=True)
        assert data == {
            "cfg": config,
            "debug": True,
            "output": exabgpctl.controller.print_yaml,
        }

        data = exabgpctl.view.create_context(output="json", debug=True)
        assert data == {
            "cfg": config,
            "debug": True,
            "output": exabgpctl.controller.print_json,
        }

        data = exabgpctl.view.create_context(output="flat", debug=True)
        assert data == {
            "cfg": config,
            "debug": True,
            "output": exabgpctl.controller.print_flat,
        }


def test_edit(runner, config):
    with patch("click.edit") as edit:
        edit.return_value = "lorem"
        result = runner.invoke(exabgpctl.view.cli, ["edit"])
        edit.assert_called_with(filename=config["path"])


def test_status(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.status_processes = MagicMock()
        exabgpctl.view.status_neighbors = MagicMock()
        result = runner.invoke(exabgpctl.view.cli, ["status"])
        exabgpctl.view.status_processes.assert_called_with(config)
        exabgpctl.view.status_neighbors.assert_called_with(config)


def test_version(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.get_version = MagicMock()

        exabgpctl.view.get_version.return_value = {"python": "1.2.3"}
        result = runner.invoke(exabgpctl.view.cli, ["version"])
        exabgpctl.view.get_version.assert_called_with(None)
        assert json.loads(result.output) == {"python": "1.2.3"}

        exabgpctl.view.get_version.return_value = "1.2.3"
        result = runner.invoke(exabgpctl.view.cli, ["version", "python"])
        exabgpctl.view.get_version.assert_called_with("python")
        assert result.output.strip() == "1.2.3"


def test_process_list(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.list_processes = MagicMock()
        exabgpctl.view.list_processes.return_value = ["one", "two"]
        result = runner.invoke(exabgpctl.view.cli, ["process", "list"])
        exabgpctl.view.list_processes.assert_called_with(config)
        assert json.loads(result.output) == ["one", "two"]

        exabgpctl.view.list_disabled_processes = MagicMock()
        exabgpctl.view.list_disabled_processes.return_value = ["one", "two"]
        result = runner.invoke(exabgpctl.view.cli, ["process", "list", "-d"])
        exabgpctl.view.list_disabled_processes.assert_called_with(config)
        assert json.loads(result.output) == ["one", "two"]


def test_process_show(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.get_process = MagicMock()
        exabgpctl.view.get_process.return_value = {"one": "two"}
        result = runner.invoke(
            exabgpctl.view.cli, ["process", "show", "service1.exabgp.lan"]
        )
        exabgpctl.view.get_process.assert_called_with(
            config, "service1.exabgp.lan"
        )
        assert json.loads(result.output) == {"one": "two"}


def test_process_enable(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.enable_process = MagicMock()
        exabgpctl.view.enable_process.return_value = True
        result = runner.invoke(
            exabgpctl.view.cli, ["process", "enable", "service1.exabgp.lan"]
        )
        exabgpctl.view.enable_process.assert_called_with(
            config, "service1.exabgp.lan"
        )
        assert bool(result.output.strip()) == True


def test_process_disable(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.disable_process = MagicMock()
        exabgpctl.view.disable_process.return_value = True
        result = runner.invoke(
            exabgpctl.view.cli, ["process", "disable", "service1.exabgp.lan"]
        )
        exabgpctl.view.disable_process.assert_called_with(
            config, "service1.exabgp.lan"
        )
        assert bool(result.output.strip()) == True


def test_state_process(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.state_process = MagicMock()
        exabgpctl.view.state_process.return_value = "UP"
        os.environ["STATE"] = "UP"
        result = runner.invoke(
            exabgpctl.view.cli, ["process", "state", "service1.exabgp.lan"]
        )
        exabgpctl.view.state_process.assert_called_with(
            config, "service1.exabgp.lan"
        )
        assert result.output.strip() == "UP"


def test_status_processes(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.status_processes = MagicMock()
        exabgpctl.view.status_processes.return_value = {
            "service1.exabgp.lan": "dict"
        }
        result = runner.invoke(exabgpctl.view.cli, ["process", "status"])
        exabgpctl.view.status_processes.assert_called_with(config)
        assert json.loads(result.output) == {"service1.exabgp.lan": "dict"}


def test_neighbor_show(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.get_neighbor = MagicMock()
        exabgpctl.view.get_neighbor.return_value = {"1.2.3.4": "dict"}
        result = runner.invoke(
            exabgpctl.view.cli, ["neighbor", "show", "1.2.3.4"]
        )
        exabgpctl.view.get_neighbor.assert_called_with(config, "1.2.3.4")
        assert json.loads(result.output) == {"1.2.3.4": "dict"}


def test_neighbor_list(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.list_neighbors = MagicMock()
        exabgpctl.view.list_neighbors.return_value = {"1.2.3.4": "dict"}
        result = runner.invoke(exabgpctl.view.cli, ["neighbor", "list"])
        exabgpctl.view.list_neighbors.assert_called_with(config)
        assert json.loads(result.output) == ["1.2.3.4"]


def test_neighbor_status(runner, config):
    with patch("exabgpctl.view.config_load") as cfg:
        cfg.return_value = config

        exabgpctl.view.status_neighbors = MagicMock()
        exabgpctl.view.status_neighbors.return_value = {"1.2.3.4": "dict"}
        result = runner.invoke(exabgpctl.view.cli, ["neighbor", "status"])
        exabgpctl.view.status_neighbors.assert_called_with(config)
        assert json.loads(result.output) == {"1.2.3.4": "dict"}
