# convenience makefile to boostrap & run buildout

version = 2.7
python = bin/python
config = development.cfg
buildout_options =

all: rebuild

docs: htdocs/sphinx

htdocs/sphinx: bin/sphinx-build docs/*.rst docs/conf.py
	bin/sphinx-build docs $@

bin/sphinx-build: .installed.cfg

rebuild: .installed.cfg
	bin/buildout $(buildout_options)

.installed.cfg: buildout.cfg bin/buildout
	bin/buildout $(buildout_options)

buildout.cfg:
	ln -s $(config) buildout.cfg

bin/buildout: buildout.cfg bootstrap.py
	$(python) bootstrap.py -d
	@touch bin/buildout

site: .installed.cfg
	bin/supervisorup ejabberd
	bin/supervisordown instance
	bin/instance create_site --rootpassword admin

fresh-site: .installed.cfg
	bin/supervisorup ejabberd
	bin/supervisordown instance
	bin/instance create_site --force --rootpassword admin

clean:
	rm -rf .installed.cfg .mr.developer.cfg \
		downloads develop-eggs eggs fake-eggs parts docs/.build

dist-clean: clean
	rm -rf bin/buildout
	git clean -x bin

.PHONY: all $(cfgs) rebuild docs clean
