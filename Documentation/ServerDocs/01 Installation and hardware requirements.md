# Hardware requirements

Keep in mind that these requirements may change in the future.

> [!IMPORTANT]
> The server has only been tested using Arch Linux, but it's expected to work using other GNU/Linux distributions.
> Windows, MacOS, and any other OS that is not GNU/Linux-based is **NOT** expected to run the server, but it might be compatible.
> 
> Do not report server-side issues if you are not running the server in a GNU/Linux OS.

## Minimum hardware requirements

These requirements are for the bare I4.0 server; no modules, no models.

- OS: GNU/Linux
- CPU: x86_64, 2 cores
- RAM: ~256 MB
- GPU: No GPU required
- Disk: 10 GB
- Python: 3.11

## Recommended hardware requirements

These requirements are for a basic I4.0 server; small models.

- OS: GNU/Linux
- CPU: x86_64, 4 or more cores
- RAM: 4 GB or more
- GPU: CUDA, ROCm, or SYCL compatible
- Disk: 30 GB
- Python: 3.11

## Testing and experimental

Currently, other CPU architectures (such as x86, ARM32, and ARM64) are being tested.
Newer Python versions are being tested, but the bare I4.0 server should be compatible. Some modules may not support newer versions.

If you try to run the I4.0 server (wether with modules or without modules) in one of the CPU architectures mentioned above, or in a newer Python version (3.12 and above), **please submit an issue telling us your experience, wether it works or not**.

# Installing Python

Follow the guide and documentation of your OS to install Python.

It is recommended to install **Python 3.11**, newer versions are being tested.

# Creating a Python VENV

It is recommended to run the server using a VENV. To create a VENV, run the following command:
```bash
python -m venv .env
```

In some Operating Systems, this command may change.

# Server installation

We recommend using the automatic installation script. This is a script that automatically installs all of the dependencies of the server and modules.

First, you have to make sure that all of the modules that you will run in the server are in the modules directory. Otherwise the requirements for those modules will not be installed.

Second, execute the `requirements.py` script. This will automatically install all the dependencies for the core server and modules.

> [!IMPORTANT]
> If a new module is added to the server after the installation, the script must be run again.

## Environment variables

TODO
