test:
	tox

fasttest:
	tox -e py36

lint:
	pylint --enable=all --disable=formatting ./exabgpctl

format:
	black -l 80 .

clean:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '*__pycache__*' -exec rm -rf {} +
	rm -rf ~/.local/share/virtualenvs/python-exabgpctl-*
	rm -rf docs/_build
