all: delete-compiled-shit upload
	echo "Done."

delete-compiled-shit:
	rm -R build/ ; rm -R luckydonald_utils.egg-info/ ; find . -name '*.pyc'
	find . -name '*.pyc' -delete ; True

upload:
	python setup.py sdist upload -r pypi
