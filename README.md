# ansible-role-container_infrastructure

[![CI](https://github.com/poppelaars/ansible-role-container_infrastructure/workflows/CI/badge.svg?branch=main&event=push)](https://github.com/poppelaars/ansible-role-container_infrastructure)

Prepares infrastructure to run container runtime software as non-root.

This role does the following:
* Create user: "container" (default);
* Enables linger mode for user;
* Installs various packages for running container software non-root;
* Configures kernel parameters;
* Configures kernel modules;
* Configures resources delegation;
* Configures bootloader;
* Enables cgroupv2.
