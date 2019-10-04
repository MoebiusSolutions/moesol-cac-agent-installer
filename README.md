DCGSN Procedures for cac-agent
================

Overview
----------------

In order to access CAC-portected HTTPS sites with software with software
that may not be CAC-enabled (Git, Maven, Eclipse, etc), we're leveraging
the [cac-agent](https://github.com/MoebiusSolutions/cac-agent) created by
Moebius Solutions.

Among other features, this provides an "cac-ssl-relay" process that can
be used to tunnel HTTP traffic through a background process that handles
the CAC-authentication.

This repo contains standard install and use instructions for Moebius Solutions
developers.

Procedures
----------------

* [Installing cac-agent](docs/Installing-cac-agent.md) (includes "cac-ssl-relay")
* [Using cac-ssl-relay](docs/Using-cac-ssl-relay.md)

