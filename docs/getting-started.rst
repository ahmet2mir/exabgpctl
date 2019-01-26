Getting started
===============

Installing exabgpctl
--------------------

exabgpctl is available on PyPI, so you can use :program:`pip`:

.. code-block:: console

    $ pip install exabgpctl

Alternatively, if you don't have setuptools installed, `download it from PyPi
<http://pypi.python.org/pypi/exabgpctl/>`_ and run

.. code-block:: console

    $ python setup.py install

To use the bleeding-edge version of exabgpctl, you can get the source from
`GitHub <http://github.com/exabgpctl/exabgpctl/>`_ and install it as above:

.. code-block:: console

    $ git clone git://github.com/ahmet2mir/exabgpctl
    $ cd exabgpctl
    $ python setup.py install

Configuration
-------------

exabgpctl will not use any "self" configuration, we will only read the real exabgp conf and extend features.
By default it will read the file under ``/etc/exabgp/exabgp.conf``.
To override it, set ``environment variable``

* ``EXABGPCTL_CONF``: exabgp.conf path (default /etc/exabgp/exabgp.conf)
* ``EXABGPCTL_STATE``: where state files should be stored (for process state command) (default /var/lib/exabgp/status)

All examples using here will use conf from ``examples`` folder.

Bash Autocompletion
-------------------

.. code-block:: console

    $ eval "$(_EXABGPCTL_COMPLETE=source exabgpctl)"

See `Click project <https://click.palletsprojects.com/en/latest/bashcomplete/>`_

Process Status
--------------

Check all process statuses, exabgpctl will read state and run the healthcheck command defined in exabgp.conf

.. code-block:: console

    $ exabgpctl process status
    {
    "service1.exabgp.lan": {
        "state": "UP",
        "command_check": "/bin/true",
        "command": true,
        "state_path": "/var/lib/exabgp/status/service1.exabgp.lan"
    }
    ...

Enable / Disable process maintenance
------------------------------------

ExaBGP support a maintenance flag, if the file exists, the route will be unannounced.

Disable

.. code-block:: console

    $ exabgpctl process disable service1.exabgp.lan
    True
    $ exabgpctl process status
    {
    "service1.exabgp.lan": {
        "state": "DISABLED",
        "command_check": "/bin/true",
        "command": true,
        "state_path": "/var/lib/exabgp/status/service1.exabgp.lan"
    }
    ...

Enable

.. code-block:: console

    $ exabgpctl process enable service1.exabgp.lan
    True
    $ exabgpctl process status
    {
    "service1.exabgp.lan": {
        "state": "UP",
        "command_check": "/bin/true",
        "command": true,
        "state_path": "/var/lib/exabgp/status/service1.exabgp.lan"
    }
    ...

List process
------------

List all process (with any state)

.. code-block:: console

    $ exabgpctl process list
    [
        "service1.exabgp.lan",
        "service2.exabgp.lan",
        "service3.exabgp.lan"
    ]

List only disabled (maintenance) process

.. code-block:: console

    $ exabgpctl process disable service1.exabgp.lan
    True
    $ exabgpctl process list -d
    [
        "service1.exabgp.lan"
    ]

Change state
------------

exabgp could update the state of the process using ``--execute`` flag in healthcheck.
And set an environment variable with the current state.

You could use exabgctl to manage this state

.. code-block:: console

    $ STATE='DOWN' exabgpctl process state service1.exabgp.lan
    DOWN
    $ exabgpctl process status
    {
    "service1.exabgp.lan": {
        "state": "DOWN",
        "command_check": "/bin/true",
        "command": true,
        "state_path": "/var/lib/exabgp/status/service1.exabgp.lan"
    }

Show process
-------------

Get process details

.. code-block:: console

    $ exabgpctl process show service1.exabgp.lan
    {
        "consolidate": false,
        "receive-keepalives": false,
        "receive-packets": false,
        "receive-opens": false,
        "receive-refresh": false,
        "receive-notifications": false,
        "neighbor-changes": false,
        "encoder": "text",
        "receive-parsed": false,
        "neighbor": "*",
        "receive-operational": false,
        "run": {
        ...

List neighbors
--------------

List all process (with any state)

.. code-block:: console

    $ exabgpctl neighbor list
    [
        "192.168.0.1",
        "192.168.0.2"
    ]

Show neighbor
-------------

Get neighbor details

.. code-block:: console

    $ exabgpctl neighbor show 192.168.0.1
    {
        "group_updates": false,
        "add_path": 0,
        "flush": true,
        "api": {},
        "connect": 0,
        "ttl": null,
        "peer_address": "192.168.0.1",
    ...

Status neighbor
---------------

Get neighbor statuses, it will try to connect to neighbor on port 179.

.. code-block:: console

    $ exabgpctl neighbor status
    {
        "192.168.0.2": {
            "status": false,
            "status_addressport": [
                "192.168.0.2",
                179
            ]
        },
        "192.168.0.1": {
            "status": false,
            "status_addressport": [
                "192.168.0.1",
                179
            ]
        }
    }
