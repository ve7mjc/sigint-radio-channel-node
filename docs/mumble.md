# Mumble Project

The client was called "Mumble" and the server "Murmer" but this has now been renamed "mumble-server" and "mumble-client" where possible.

# Mumble Server

## Configuration (mumble-server.ini / murmer.ini)

Project Example: https://github.com/mumble-voip/mumble/blob/master/auxiliary_files/mumble-server.ini
https://wiki.mumble.info/wiki/Murmur.ini


## docker-mumble

https://hub.docker.com/r/phlak/mumble


## PyMumble (Client Library)

- *Warning*: `pymumble` has a number of deficiencies and is **DEPRECATED** (2024-12)

- Project: https://github.com/azlux/pymumble
- API Docs: https://github.com/azlux/pymumble/blob/pymumble_py3/API.md

### Key Problems

- TCP audio streams only!
  - this was the case with the QRadioLink project ~ 2016 also - and suspect it is due to a different encryption schema
  - The TCP audio streams lean on the TLS wrapper contexts over basic sockets


