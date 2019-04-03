all: delete-compiled-shit pip git
	echo "Done."

delete-compiled-shit:
	rm -R build/ ; rm -R luckydonald_utils.egg-info/ ; find . -name '*.pyc'
	find . -name '*.pyc' -delete ; True

upload: pip git

pip-build:
	python3 setup.py sdist bdist_wheel

test-pip: pip-build
	python3 -m twine upload --username luckydonald --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

pip: pip-build
	python3 -m twine upload --username luckydonald --skip-existing dist/*

git:
	git push
