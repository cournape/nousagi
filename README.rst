==================================
 nousagi: CLI test plugin for haas
==================================

``nousagi`` is a plugin for haas_ that adds support for discovering CLI test
cases descibed in YAML.

It supports the following features:

  * semi-declarative description of CLI behaviour
  * supports both individual tests or scenarios for more complex behaviour
  * output, status code, file existence assertions
  * simple variable system
  * pre-defined set of functions to apply before running a test: injecting
    environment variables, creating temporary files and directories 

Once the core set of features is stabilized, we will focus on making nousagi
more extensible (adding custom assertions and functions to apply before/after
running tests)

``nousagi`` requires ``haas v0.6.0`` or later.


.. _haas: https://github.com/sjagoe/haas

Examples
========

Tests are organized as cases, following python's unittest convention::

  # test_git.yml
  cases:
    - name: "tests without a command"
      tests:
        - name: "Test 'git' runs"
          cmd: "git"
          status: 1

To execute this test, simpley run::

    $ haas --discover nousagi test_git.yml
    [Tue Aug  4 09:00:36 2015] (1/1) "tests without a command:Test 'git' runs" (/home/davidc/src/enthought/nousagi-git/test_git.yml) ... ok

You can organize multiple tests in one case, e.g.::

  cases:
    - name: "tests without a command"
      tests:
        - name: "Test 'git' runs"
          cmd: "git"
          status: 1

        - name: "Test 'git --version' runs"
          cmd: "git --version"
          status: 0

Checking for output
-------------------

You can check for a specific command output using assertions::

    cases:
      - name: "tests without a command"
        tests:
          - name: "Test 'git --version' runs"
            cmd: "git --version"
            status: 0
            assertions:
              - type: regex
                expected: 'git version (\d+)(\.\d+)*'
