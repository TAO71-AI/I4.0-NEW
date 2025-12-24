from setuptools import setup, find_packages

setup(
    name = "I4_0-Client-PY",
    version = "17.0.0",
    description = "Python bindings for I4.0, Client-side.",
    author = "TAO71-AI",
    url = "https://github.com/TAO71-AI/I4.0-NEW",
    packages = find_packages(include = ["I4_0_Client", "I4_0_Client.*"]),
    include_package_data = True,
    license = "TAO71 I4.0 License (version 2)",
    install_requires = [
        "websockets>=15.0.0,<16.0.0",
        "asyncio",
        "cryptography"
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent"
    ],
    python_requires = ">=3.11",
    project_urls = {
        "Source": "https://github.com/TAO71-AI/I4.0-NEW/tree/master/Client/",
        "License": "https://github.com/TAO71-AI/I4.0-NEW/blob/master/LICENSE.md"
    }
)