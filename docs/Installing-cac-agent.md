Installing cac-agent
================

Prerequisite - Java
----------------

On both Linux and Windows you'll need Java 8 or 11 (LTS releases).

* Java 9 is specifically known to **not** be compatible.

You'll want to make sure java's execute is on your default `PATH`,
which is likely an extra step on Windows but not Linux.


Prerequisite - Middleware
----------------

On Linux, you'll need PCSC and the OpenSC middleware in order to
interact with DoD Smart Cards:

	sudo apt install pcscd pcsc-tools opensc

On Windows 10, no additional middleware is required for DoD Smart Cards.


Prerequisite - Admin Access
----------------

In order to configure the "cac-ssl-relay" feature of cac-agent, you'll
need admin access to your machine. This is necessary in order to modify
your `hosts` file.

In the case of Linux, you'll need to have access to `sudo`.

In the case of Window, you'll be prompted to login as a user with
admin privileges as necessary.


Prerequisite - Python
----------------

The installation script requires Python.

Linux generally comes with Python installed, but ensure that you have `python3`:

	python3 --version

Windows requires manually install of Python. The easiest way to get this
is to download and extract the `Windows x86 embeddable zip file` (no admin
needed) from:

* [Python.org Downloads](https://www.python.org/downloads/windows/)


Clone this Repo
----------------

You can clone this repo:

	git clone https://github.com/MoebiusSolutions/moesol-cac-agent-installer.git


Install on Linux
----------------

Execute the install script from the cloned/copied repo:

	cd moesol-cac-agent-installer/
	python3 install-cac-agent.py

Provide your credentials when prompted to run `sudo` actions.


Install on Windows
----------------

Execute the install script from the cloned/copied repo:

	cd moesol-cac-agent-installer
	c:\path\to\python.exe install-cac-agent.py

Provide appropriate credentials to admin actions when prompted.

