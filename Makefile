all: delete-compiled-shit pip git
	echo "Done."

delete-compiled-shit:
	rm -R build/ ; rm -R luckydonald_utils.egg-info/ ; find . -name '*.pyc'
	find . -name '*.pyc' -delete ; True

delete-old-dist:
	find dist -name '*' -delete ; True

upload: pip git

pip-build: delete-old-dist
	python3 setup.py sdist bdist_wheel

dev-dependencies:
	python3 -m pip install -r requirements-dev.txt

test-pip: pip-build dev-dependencies
	python3 -m twine upload --username luckydonald --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

pip: pip-build
	python3 -m twine upload --username luckydonald --skip-existing dist/*

git:
	git push

bump: dev-dependencies
	bump-my-version show-bump
	bump-my-version bump patch
