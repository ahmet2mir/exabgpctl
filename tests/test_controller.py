# -*- coding: utf-8 -*-
# standard
import os
import json
import shutil
import tempfile

# third
import yaml
import pytest
from mock import patch, MagicMock

# local
from exabgpctl import controller, _py6


@pytest.fixture
def config():
    if _py6.PY2:
        os.environ["EXABGPCTL_CONF"] = os.path.abspath("examples/exabgp3.conf")
    else:
        os.environ["EXABGPCTL_CONF"] = os.path.abspath("examples/exabgp4.conf")

    os.environ["EXABGPCTL_STATE"] = "/tmp"

    return controller.config_load()


def test_get_version():
    controller.platform = MagicMock()
    controller.platform.python_version.return_value = "3.7.1"
    controller.platform.platform.return_value = (
        "Linux-4.4.0-138-generic-x86_64-with"
    )
    controller.platform.close.return_value = True

    assert controller.get_version()["python"] == "3.7.1"
    assert (
        controller.get_version()["os"] == "Linux-4.4.0-138-generic-x86_64-with"
    )
    assert controller.get_version("python") == "3.7.1"


def test_config_load(tmpdir):
    os.environ["EXABGPCTL_CONF"] = "raise"
    with pytest.raises(controller.ExabgpCTLError):
        controller.config_load()

    os.environ["EXABGPCTL_CONF"] = str(tmpdir)
    os.environ["EXABGPCTL_STATE"] = "raise"
    with pytest.raises(controller.ExabgpCTLError):
        controller.config_load()

    if _py6.PY2:
        os.environ["EXABGPCTL_CONF"] = os.path.abspath("examples/exabgp3.conf")
    else:
        os.environ["EXABGPCTL_CONF"] = os.path.abspath("examples/exabgp4.conf")
    os.environ["EXABGPCTL_STATE"] = str(tmpdir)
    data = controller.config_load()

    assert data["state"] == os.environ["EXABGPCTL_STATE"]
    assert data["path"] == os.environ["EXABGPCTL_CONF"]
    assert data["version"] == controller.get_version()

    assert data["version"] == controller.get_version()
    assert sorted([item["name"] for item in data["processes"]]) == [
        "service1.exabgp.lan",
        "service2.exabgp.lan",
        "service3.exabgp.lan",
    ]
    assert sorted([item["name"] for item in data["neighbors"]]) == [
        "192.168.0.1",
        "192.168.0.2",
    ]


def test_tcping():
    controller.socket = MagicMock()

    controller.socket.socket().connect_ex.return_value = 1
    assert controller.tcping("localhost", "1234") == (False, 1)

    controller.socket.socket().connect_ex.return_value = 0
    assert controller.tcping("localhost", "1234") == (True, 0)

    controller.socket.socket().connect_ex.side_effect = RuntimeError(
        "General Error!"
    )
    assert controller.tcping("localhost", "1234") == (False, -1)


def test_flat():
    data = {
        "key1": {
            "key11": {"key111": "value111"},
            "key12": {"key121": [{"key1211": "value1211"}]},
        },
        "key2": ["one", "two", "three"],
    }

    expected = {
        "key1__key11__key111": "value111",
        "key1__key12__key121[0]__key1211": "value1211",
        "key2[0]": "one",
        "key2[1]": "two",
        "key2[2]": "three",
    }

    assert controller.flat(data) == expected


def test_print(capsys):
    data = {
        "key1": {
            "key11": {"key111": "value111"},
            "key12": {"key121": [{"key1211": "value1211"}]},
        },
        "key2": ["one", "two", "three"],
    }

    exp_flat = """key1__key11__key111=value111
key1__key12__key121[0]__key1211=value1211
key2[0]=one
key2[1]=two
key2[2]=three
"""

    controller.print_json(data)
    out, err = capsys.readouterr()
    assert json.loads(out) == data

    controller.print_json("data")
    out, err = capsys.readouterr()
    assert out == "data\n"

    controller.print_yaml(data)
    out, err = capsys.readouterr()
    assert yaml.load(out) == data

    controller.print_yaml("data")
    out, err = capsys.readouterr()
    assert out == "data\n"

    controller.print_flat(data)
    out, err = capsys.readouterr()
    assert out == exp_flat

    controller.print_flat("data")
    out, err = capsys.readouterr()
    assert out == "data\n"


def test_list_processes(config):
    assert sorted(controller.list_processes(config)) == [
        "service1.exabgp.lan",
        "service2.exabgp.lan",
        "service3.exabgp.lan",
    ]


def test_get_process(config):
    name = config["processes"][0]["name"]
    assert controller.get_process(config, name)["name"] == name
    assert (
        controller.get_process(config, name)["run"]["disable"]
        == "/tmp/exabgp/maintenance/%s" % name
    )

    with pytest.raises(controller.ExabgpCTLError):
        controller.get_process(config, "raise")


def test_disabled_processes(config):
    name = config["processes"][0]["name"]
    config["processes"][0]["run"]["disable"] = "/tmp/maintenance_%s" % name

    assert controller.list_disabled_processes(config) == []
    assert name in controller.list_enabled_processes(config)

    assert controller.disable_process(config, name) == True
    # already disabled
    assert controller.disable_process(config, name) == True
    assert controller.list_disabled_processes(config) == [name]
    assert name not in controller.list_enabled_processes(config)

    assert controller.enable_process(config, name) == True
    # already enabled
    assert controller.enable_process(config, name) == True
    assert controller.list_disabled_processes(config) == []
    assert name in controller.list_enabled_processes(config)


def test_state_process(config):
    name = config["processes"][0]["name"]

    os.environ["STATE"] = "UP"
    assert controller.state_process(config, name) == "UP"

    os.environ["STATE"] = "DOWN"
    assert controller.state_process(config, name) == "DOWN"

    os.unlink(config["state"] + "/" + name)


def test_status_processes(config):

    config["processes"][0]["run"]["command"] = "/bin/true"
    os.environ["STATE"] = "UP"
    assert controller.state_process(config, config["processes"][0]["name"])

    config["processes"][1]["run"]["command"] = "/bin/false"
    os.environ["STATE"] = "DOWN"
    assert controller.state_process(config, config["processes"][1]["name"])

    config["processes"][2]["run"]["command"] = "/bin/false"

    expected = {
        config["processes"][0]["name"]: {
            "state": "UP",
            "state_path": "/tmp/%s" % config["processes"][0]["name"],
            "command": True,
            "command_check": "/bin/true",
        },
        config["processes"][1]["name"]: {
            "state": "DOWN",
            "state_path": "/tmp/%s" % config["processes"][1]["name"],
            "command": False,
            "command_check": "/bin/false",
        },
        config["processes"][2]["name"]: {
            "state": "UNKNOWN",
            "state_path": "/tmp/%s" % config["processes"][2]["name"],
            "command": False,
            "command_check": "/bin/false",
        },
    }
    assert controller.status_processes(config) == expected

    try:
        os.unlink("/tmp/%s" % config["processes"][0]["name"])
    except:
        pass

    try:
        os.unlink("/tmp/%s" % config["processes"][1]["name"])
    except:
        pass

    try:
        os.unlink("/tmp/%s" % config["processes"][2]["name"])
    except:
        pass


def test_list_neighbors(config):
    assert sorted(controller.list_neighbors(config)) == [
        "192.168.0.1",
        "192.168.0.2",
    ]


def test_get_neighbor(config):
    assert (
        controller.get_neighbor(config, "192.168.0.1")["name"] == "192.168.0.1"
    )
    with pytest.raises(controller.ExabgpCTLError):
        controller.get_neighbor(config, "raise")


def test_status_neighbors(config):
    controller.tcping = MagicMock()
    controller.tcping.return_value = (True, 0)

    expected = {
        "192.168.0.1": {
            "status": True,
            "status_addressport": ["192.168.0.1", 179],
        },
        "192.168.0.2": {
            "status": True,
            "status_addressport": ["192.168.0.2", 179],
        },
    }

    assert controller.status_neighbors(config) == expected
