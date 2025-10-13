import Utilities.install_requirements as requirements

GENERAL_REQUIREMENTS = [
    "PyYAML",
    "requests",
    "beautifulsoup4",
    "tiktoken",
    "pydub",
    "websockets>=15.0.0,<16.0.0"
]
requirements.InstallPackage(GENERAL_REQUIREMENTS)

import services_manager as servMgr
servMgr.InstallAllRequirements()