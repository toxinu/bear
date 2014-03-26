test:
	python tests/run_tests.py
coverage:
	nosetests --with-coverage --cover-package bear --cover-html --cover-inclusive bear/plugins*
