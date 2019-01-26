# -*- coding: utf-8 -*-
"""
exabgpctl.view
~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, print_function

# standard
import os
import sys
import json
import socket
import platform
import collections

# third
import yaml
from yaml.representer import SafeRepresenter
from exabgp.application import healthcheck
from exabgp.configuration.setup import environment
from exabgp.version import version as exabgp_version

try:
    from exabgp.configuration.ancient import Configuration
except:
    from exabgp.configuration.configuration import Configuration

# local
from exabgpctl.release import __version__ as exabgpctl_version
from exabgpctl._py6 import (
    iteritems,
    iterkeys,
    itervalues,
    string_types,
    text_type,
)


class ExabgpCTLError(Exception):
    """Generic Error to catch from view"""


def config_load():
    """ExaBGP config loader.
    Loader will use exabgp lib to load the config like exabgp did

    Returns:
        dict: configuration with path, state, version, neighbors and processes.

    Examples:
        >>> import os
        >>> os.environ['EXABGPCTL_CONF'] = "/etc/exabgp/exabgp.conf"
        >>> os.environ['EXABGPCTL_STATE'] = "/var/lib/exabgp/state"
        >>> cfg = config_load()
        >>> cfg
        {
            'path': '/tmp/exabgp/exabgp.conf',
            'state': '/tmp/exabgp/state',
            'version': {
                'python': '3.7.1',
                'exabgp': '3.4.19',
                'os': 'Linux-4.4.0-138-generic-x86_64-with',
                'exabgpctl': '19.01-1'
            },
            'neighbors': [
                {
                    'local_address': '192.168.1.1',
                    'local_as': 12345,
                    'name': '192.168.0.1',
                    'peer_address': '192.168.0.1',
                    'peer_as': 67890,
                    'router_id': '192.168.1.1',
                    ...
                },
                {
                    'local_address': '192.168.1.1',
                    'local_as': 12345,
                    'name': '192.168.0.1',
                    'peer_address': '192.168.0.1',
                    'peer_as': 67890,
                    'router_id': '192.168.1.1',
                    ...
                }
            ],
            'processes': [
            {
                'name': 'service1.exabgp.lan',
                'run': {
                    'ip_dynamic': False,
                    'disabled_execute': None,
                    'sudo': False,
                    'pid': None,
                    'community': '11223:344',
                    'withdraw_on_down': True,
                    'execute': ['/usr/bin/exabgpctl process state service1...'],
                    'name': 'service1.exabgp.lan',
                    'interval': 5,
                    'disable': '/tmp/exabgp/maintenance/service1.exabgp.lan',
                    'command': '/bin/mycheck',
                    'timeout': 5,
                    ...
                },
                ...
            },
            {
                'name': 'service2.exabgp.lan',
                'run': {
                    'ip_dynamic': False,
                    'disabled_execute': None,
                    'sudo': False,
                    'pid': None,
                    'community': '11223:355',
                    'withdraw_on_down': True,
                    'execute': ['/usr/bin/exabgpctl process state service2...'],
                    'name': 'service2.exabgp.lan',
                    'interval': 5,
                    'disable': '/tmp/exabgp/maintenance/service2.exabgp.lan',
                    'command': '/bin/mycheck',
                    'timeout': 5,
                    ...
                },
                ...
            },
            {
                'name': 'service3.exabgp.lan',
                'run': {
                    'ip_dynamic': False,
                    'disabled_execute': None,
                    'sudo': False,
                    'pid': None,
                    'community': '11223:366',
                    'withdraw_on_down': True,
                    'execute': ['/usr/bin/exabgpctl process state service3...'],
                    'name': 'service3.exabgp.lan',
                    'interval': 5,
                    'disable': '/tmp/exabgp/maintenance/service3.exabgp.lan',
                    'command': '/bin/mycheck',
                    'timeout': 5,
                    ...
                },
                ...
            }
            ]
        }

    Raises:
        ExabgpCTLError: if the conf file doesn't exists.

    See Also:
        github.com/Exa-Networks/exabgp/qa/tests/parsing_test.py
    """
    environ = environment.setup("")
    environ.log.enable = True
    environ.log.all = False
    environ.log.configuration = False
    environ.log.parser = False

    path = os.environ.get("EXABGPCTL_CONF", "/etc/exabgp/exabgp.conf")
    state = os.environ.get("EXABGPCTL_STATE", "/var/lib/exabgp/status")

    if not os.path.exists(path):
        raise ExabgpCTLError("ExaBGP conf file %s doesn't exists" % str(path))

    if not os.path.exists(state):
        raise ExabgpCTLError("ExaBGP state dir %s doesn't exists" % str(state))

    cfg = Configuration([os.path.abspath(path)])
    cfg.reload()

    result = {
        "path": path,
        "state": state,
        "processes": [],
        "neighbors": [],
        "version": get_version(),
    }

    if isinstance(cfg.process, dict):
        _processes = cfg.process
    else:
        _processes = cfg.__dict__["processes"]

    if isinstance(cfg.neighbor, dict):
        _neighbors = cfg.neighbor
    else:
        _neighbors = cfg.__dict__["neighbors"]

    sys_argv = sys.argv
    for svc, params in iteritems(_processes):
        item = params.copy()
        sys.argv = params["run"]
        item["run"] = healthcheck.parse().__dict__
        ips = {}
        for ipaddr in item["run"]["ips"]:
            ips.update(_parse_ip(ipaddr))
        item["run"]["ips"] = ips
        item["run"]["next_hop"] = _parse_ip(item["run"]["next_hop"])
        item["name"] = svc
        result["processes"].append(item)
    sys.argv = sys_argv

    for neighbor in itervalues(_neighbors):
        item = neighbor.__dict__.copy()
        item.pop("_families")
        item.update(
            {
                "name": str(neighbor.peer_address),
                "rib": str(neighbor.rib.name),
                "messages": list(neighbor.messages),
                "refresh": list(neighbor.refresh),
                "eor": list(neighbor.eor),
                "local_address": str(neighbor.local_address),
                "local_as": int(neighbor.local_as),
                "peer_as": int(neighbor.peer_as),
                "peer_address": str(neighbor.peer_address),
                "router_id": str(neighbor.router_id),
            }
        )
        result["neighbors"].append(item)

    return result


def get_version(key=None):
    """Get module, deps and platform version informations.

    Args:
        key (str): filter item

    Returns:
        dict: With exabgp, exabgctl, python and os versions. If key specified
              will return a string.

    Examples:
        >>> get_version()
        {
            'python': '3.7.1',
            'exabgp': '3.4.19',
            'os': 'Linux-4.4.0-138-generic-x86_64-with',
            'exabgpctl': '19.01-1'
        }
        >>> get_version("exabgpctl")
        '19.01-1'
    """
    data = {
        "exabgp": exabgp_version,
        "exabgpctl": exabgpctl_version,
        "python": platform.python_version(),
        "os": platform.platform(),
    }
    if key:
        return data[key]
    return data


def tcping(address, port):
    """Like tcping tools, will test if the address:port is open.

    Args:
        address (str): target address ip.
        port (int): target port.

    Returns:
        bool: True if address:port is open.

    Examples:
        >>> tcping('8.8.8.8', 53)
        True
    """
    result = 1
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((address, port))
    # catch all errors
    # pylint: disable=broad-except
    except Exception as err:
        print(err)
        result = -1
    finally:
        sock.close()

    return (result == 0, result)


def flat(data, prefix=None):
    """Flat the dict

    Args:
        data (dict): the dict to flat. Must be a key/value dict.
        prefix (str, optional): prefix key with a str value, defaults is None.

    Returns:
        dict: flatted dict

    Examples:
        >>> data = {
                "key1": {
                    "key11": {
                        "key111": "value111"
                    },
                    "key12": {
                        "key121": "value121"
                    }
                },
                "key2": ["one","two", "three"]
            }
        >>> flat(data)
        {
            'key1_key11_key111': 'value111',
            'key1_key12_key121': 'value121',
            'key2[1]': 'two',
            'key2[2]': 'three',
            'key2[0]': 'one'
        }

    See Also:
        * github.com/ahmet2mir/python-snippets/snippets/flat_unflat_dict.py
    """
    separator = "__"
    lseparator = ("[", "]")
    items = []
    for k in sorted(data.keys()):
        new_key = k
        if prefix:
            new_key = prefix + separator + k
        if isinstance(data[k], dict):
            items.extend(flat(data[k], new_key).items())
        else:
            if isinstance(data[k], list):
                for i, value in enumerate(data[k]):
                    pkey = new_key + lseparator[0] + str(i) + lseparator[1]
                    if isinstance(value, collections.MutableMapping):
                        flated = flat(value, pkey)
                        items.extend(flated.items())
                    else:
                        items.append((pkey, value))
            else:
                items.append((new_key, data[k]))

    return dict(items)


def print_flat(data):
    """Print data in flat mode.

    If data is not hash or list, will only print raw value.

    Args:
        data (dict): data to print.

    Examples:
        >>> data = {
                "key1": {
                    "key11": {
                        "key111": "value111"
                    },
                    "key12": {
                        "key121": "value121"
                    }
                },
                "key2": ["one","two", "three"]
            }
        >>> print_flat(data)
        key1__key11__key111=value111
        key1__key12__key121=value121
        key2[0]=one
        key2[1]=two
        key2[2]=three
    """
    if not isinstance(data, dict) and not isinstance(data, list):
        print(data)
    else:
        flat_data = flat(data)
        for key in sorted(iterkeys(flat_data)):
            print("{}={}".format(key, flat_data[key]))


def print_json(data):
    """Print data in json mode.

    If data is not hash or list, will only print raw value.

    Args:
        data (dict): data to print.

    Examples:
        >>> data = {
                "key1": {
                    "key11": {
                        "key111": "value111"
                    },
                    "key12": {
                        "key121": "value121"
                    }
                },
                "key2": ["one","two", "three"]
            }
        >>> print_json(data)
        {
            "key2": [
                "one",
                "two",
                "three"
            ],
            "key1": {
                "key12": {
                    "key121": "value121"
                },
                "key11": {
                    "key111": "value111"
                }
            }
        }
    """
    if not isinstance(data, dict) and not isinstance(data, list):
        print(data)
    else:
        print(json.dumps(data, indent=4))


def print_yaml(data):
    """Print data in yaml mode.

    If data is not hash or list, will only print raw value.

    Args:
        data (dict): data to print.

    Examples:
        >>> data = {
                "key1": {
                    "key11": {
                        "key111": "value111"
                    },
                    "key12": {
                        "key121": "value121"
                    }
                },
                "key2": ["one","two", "three"]
            }
        >>> print_yaml(data)
        ---
        key1:
          key11:
            key111: value111
          key12:
            key121: value121
        key2:
          - one
          - two
          - three
    """
    # Hack to enhance Yaml dump ident and unicode
    class MyDumper(yaml.Dumper):  # pylint: disable=too-many-ancestors
        """Extend yaml dumper to print better indent on list"""

        def increase_indent(self, flow=False, indentless=False):
            return super(MyDumper, self).increase_indent(flow, False)

    if not isinstance(data, dict) and not isinstance(data, list):
        print(data)
    else:
        MyDumper.add_representer(string_types, SafeRepresenter.represent_str)
        if hasattr(SafeRepresenter, "represent_unicode"):
            MyDumper.add_representer(
                text_type, SafeRepresenter.represent_unicode
            )
        print("---")
        print(
            yaml.dump(
                data, default_flow_style=False, width=179, Dumper=MyDumper
            )
        )


def _parse_ip(ipaddr):
    """Parse ExaBGP IP type."""
    return {
        ipaddr.compressed: {
            "compressed": str(ipaddr.compressed),
            "exploded": str(ipaddr.exploded),
            "is_link_local": ipaddr.is_link_local,
            "is_loopback": ipaddr.is_loopback,
            "is_multicast": ipaddr.is_multicast,
            "is_private": ipaddr.is_private,
            "is_reserved": ipaddr.is_reserved,
            "is_unspecified": ipaddr.is_unspecified,
            "max_prefixlen": ipaddr.max_prefixlen,
            "reverse_pointer": getattr(ipaddr, "reverse_pointer", ""),
            "version": ipaddr.version,
        }
    }


def list_processes(cfg):
    """List processes from config.

    Args:
        cfg (dict): config from config_load.

    Returns:
        list: list of string with process names.

    Examples:
        >>> list_processes(cfg)
        ['service1.exabgp.lan', 'service2.exabgp.lan', 'service3.exabgp.lan']
    """
    return [process["name"] for process in cfg["processes"]]


def get_process(cfg, name):
    """Show process details.

    Args:
        cfg (dict): config from config_load.
        name (str): process to retrieve.

    Returns:
        dict: process data.

    Examples:
        >>> get_process(cfg, 'service1.exabgp.lan')
        {
            'name': 'service1.exabgp.lan',
            'run': {
                'ip_dynamic': False,
                'disabled_execute': None,
                'sudo': False,
                'pid': None,
                'community': '11223:344',
                'withdraw_on_down': True,
                'name': 'service1.exabgp.lan',
                'interval': 5,
                'disable': '/tmp/exabgp/maintenance/service1.exabgp.lan',
                'command': '/bin/mycheck',
                'timeout': 5,
                ...
            },
            ...
        }

    Raises:
        ExabgpCTLError: If process not found.
    """
    for process in cfg["processes"]:
        if name == process["name"]:
            return process
    raise ExabgpCTLError("Process %s not found" % name)


def list_disabled_processes(cfg):
    """List disabled processes from config.

    Args:
        cfg (dict): config from config_load.

    Returns:
        list: list of string with process names.

    Examples:
        >>> list_disabled_processes(cfg)
        ['service1.exabgp.lan']
    """
    return [
        process["name"]
        for process in cfg["processes"]
        if os.path.exists(process["run"]["disable"])
    ]


def list_enabled_processes(cfg):
    """List enabled processes from config.

    Args:
        cfg (dict): config from config_load.

    Returns:
        list: list of string with process names.

    Examples:
        >>> list_enabled_processes(cfg)
        ['service2.exabgp.lan', 'service3.exabgp.lan']
    """
    disabled = list_disabled_processes(cfg)
    return [
        process for process in list_processes(cfg) if process not in disabled
    ]


def disable_process(cfg, process):
    """Disable process (ie create maintenance file).

    Args:
        cfg (dict): config from config_load.
        process (str): process to disable.

    Returns:
        bool: True if the file exists.

    Examples:
        >>> disable_process(cfg, 'service1.exabgp.lan')
        True
        >>> list_disabled_processes(cfg)
        ['service1.exabgp.lan']
    """
    path = get_process(cfg, process)["run"].get("disable")
    if path and not os.path.exists(path):
        with open(path, "a"):
            os.utime(path, None)
    return os.path.exists(path)


def enable_process(cfg, process):
    """Enable process (ie create maintenance file).

    Args:
        cfg (dict): config from config_load.
        process (str): process to enable.

    Returns:
        bool: True if the file exists.

    Examples:
        >>> list_disabled_processes(cfg)
        ['service1.exabgp.lan']
        >>> enable_process(cfg, 'service1.exabgp.lan')
        True
        >>> list_disabled_processes(cfg)
        []
    """
    path = get_process(cfg, process)["run"].get("disable")
    if path and os.path.exists(path):
        os.unlink(path)
    return not os.path.exists(path)


def state_process(cfg, process):
    """Set exabgp state in a statefile.

    ExaBGP healthcheck command could run an action on each state change using
    environment called "STATE". See healthcheck --execute option.


    Args:
        cfg (dict): config from config_load.
        process (str): process to enable.

    Returns:
        str: One of exabgp stat
            INIT:     Initial state
            DISABLED: Disabled state
            RISING:   Checks are currently succeeding.
            FALLING:  Checks are currently failing.
            UP:       Service is considered as up.
            DOWN:     Service is considered as down.

    Examples:
        >>> import os
        >>> os.environ["STATE"] = "UP"
        >>> state_process(cfg, 'service1.exabgp.lan')
        'UP'
        >>> with open(cfg["state"] + "/service1.exabgp.lan", "r") as fd:
        ...     fd.read()
        'UP'
    """
    target = "%s/%s" % (cfg["state"], process)
    state = os.environ.get("STATE", "no state found")
    with open(target, "w") as fds:
        fds.write(state)
    return state


def status_processes(cfg):
    """Read all states from statefiles and run using healthcheck commands.

    Args:
        cfg (dict): config from config_load.
        process (str): process to enable.

    Returns:
        dict: with statuses for each process.

    Examples:
        >>> status_processes(cfg)
        {
            'service1.exabgp.lan': {
                'state': 'UP',
                'state_path': '/tmp/exabgp/state/service1.exabgp.lan',
                'command': True,
                'command_check': '/bin/mycheck'
            },
            'service2.exabgp.lan': {
                'state': 'DOWN',
                'state_path': '/tmp/exabgp/state/service2.exabgp.lan',
                'command': False,
                'command_check': '/bin/mycheck'
            },
            'service3.exabgp.lan': {
                'state': 'DOWN',
                'state_path': '/tmp/exabgp/state/service3.exabgp.lan',
                'command': False,
                'command_check': '/bin/mycheck'
            }
        }
    """
    result = {}
    for process in cfg["processes"]:
        state = "UNKNOWN"
        path = "%s/%s" % (cfg["state"], process["name"])
        if os.path.exists(path):
            with open(path) as fds:
                state = fds.read().strip()
        cmd = healthcheck.check(
            process["run"]["command"], process["run"]["timeout"]
        )
        result[process["name"]] = {
            "state": state,
            "state_path": path,
            "command": cmd,
            "command_check": process["run"]["command"],
        }
    return result


def list_neighbors(cfg):
    """List neighbors from config.

    Args:
        cfg (dict): config from config_load.

    Returns:
        list: list of string with neighbor names.

    Examples:
        >>> list_neighbors(cfg)
        ['192.168.0.2', '192.168.0.1']
    """
    return [neighbor["name"] for neighbor in cfg["neighbors"]]


def get_neighbor(cfg, name):
    """Show neighbor details.

    Args:
        cfg (dict): config from config_load.
        name (str): neighbor to retrieve.

    Returns:
        dict: neighbor data.

    Examples:
        >>> get_neighbor(cfg, '192.168.0.2')
        {
            'local_address': '192.168.1.1',
            'local_as': 12345,
            'name': '192.168.0.1',
            'peer_address': '192.168.0.1',
            'peer_as': 67890,
            'router_id': '192.168.1.1',
            ...
        }

    Raises:
        ExabgpCTLError: If neighbor not found.
    """
    for neighbor in cfg["neighbors"]:
        if name == neighbor["name"]:
            return neighbor
    raise ExabgpCTLError("Neighbor %s not found" % name)


def status_neighbors(cfg):
    """Check connectivity with neighbors.

    Args:
        cfg (dict): config from config_load.

    Returns:
        dict: with statuses for each neighbor.

    Examples:
        >>> status_neighbors(cfg)
        {
            '192.168.0.1': {
                'status': True,
                'status_addressport': ['192.168.0.1', 179]
            },
            '192.168.0.2': {
                'status': True,
                'status_addressport': ['192.168.0.2', 179]
            }
        }
    """
    result = {}
    for neighbor in cfg["neighbors"]:
        result[neighbor["name"]] = {
            "status": tcping(neighbor["peer_address"], 179)[0],
            "status_addressport": [neighbor["peer_address"], 179],
        }
    return result
