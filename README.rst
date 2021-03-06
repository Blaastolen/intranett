Documentation
=============

Prerequisites
-------------

In addition to Git and Python, you need to have Ruby, Erlang and some stuff
installed. Via MacPorts install:

    pcre
    pkgconfig
    rb19-haml
    erlang

Tests
-----

You can run tests for all packages at once using::

  bin/test

In order to run coverage tests, which includes upgrade tests use::

  bin/coverage
  bin/report-html

You can view the coverage results in the htmlcov directory via::

  open htmlcov/index.html

Site creation
-------------

To create a Plone site in the database call::

  bin/instance create_site

To overwrite an existing site and set the admin password, you can use::

  bin/instance create_site --force --rootpassword=admin --language=no

Working on a ticket
-------------------

If you work on a non-trivial story ticket, you should create a branch of this
buildout. The Git master should always be in a releasable state to the
production environment.

As a convention we use the ticket number and a short word or two to describe
each ticket.

For example, if you want to work on ticket #82, called ``Special view for the
frontpage``, here's the steps you should take::

  git co -b 82-frontpage

Edit the any config files you need to get new software (if any) and run::

  bin/buildout

You are now working on your own branch and can pull in additional dependencies
if you want to. Push the branch to Github for other people to see it::

  g push -u

You only need to specify the `-u` the first time, to associate your local
branch with the remote one.

After the ticket is done, all tests are written, it's been tested TTW,
upgrade notes or automatic steps are in place and quality assurance has been
performed, you can request the release manager to merge your branch to master.


Working with CSS
----------------

We are using `SASS <http://sass-lang.com/>`_ to generate our CSS files. On Mac
OS use macports to install it::

  sudo port install rb19-haml

The Ruby 1.8 version available via `rb-haml` is too outdated for our purposes.

To update all CSS files from their SCSS source files, call::

  sass --update src/intranett.theme/intranett/theme/skins/intranett_theme_styles:src/intranett.theme/intranett/theme/skins/intranett_theme_styles


I18N
----

To update the translation files, do::

  sh src/intranett.policy/intranett/policy/rebuild.sh
  sh src/intranett.policy/intranett/policy/sync.sh


Upgrades
--------

Add a new upgrade handler at the bottom of the upgrades.steps module. Use the
next integer available in the ``@upgrade_to(42)`` decorator. The upgrade
handler is called with the `portal_setup` tool as the context.

You also need to add a test to `upgrades.tests`. You can write a `before_42`
and `after_42` method. They will be called with a real site being migrated to
the point `before` and `after` your upgrade step is run.

There's no other places involved - neither ZCML nor metadata.xml files.


Email
-----

If you need to work on email related tasks, you can use the `bin/debugsmtp`
script. It starts a simple mail server which dumps all received mails to the
console. The text is quoted, so replace `=3D` by `=` and remove `=` on the line
endings.

To use it go to `http://localhost:8080/Plone/@@mail-controlpanel` and change
the mail server to be `localhost` on port `8025`.
