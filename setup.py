# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Exabgp Controller

Licence
```````
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
__author__ = "Ahmet Demir <me@ahmet2mir.eu>"

from setuptools import setup, find_packages

from exabgpctl.release import __version__

setup(
    name="exabgpctl",
    version=__version__,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ahmet2mir/exabgpctl.git",
    author="Ahmet Demir",
    author_email="me@ahmet2mir.eu",
    description="ExaBGP admin CLI",
    license="Apache 2.0",
    keywords=["exabgpctl", "command line", "cli", "ssh", "r10k"],
    packages=find_packages(),
    package_data={"": ["README.md"]},
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={"console_scripts": ["exabgpctl = exabgpctl.view:main"]},
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
    ],
)
