import Utilities.install_requirements as requirements

GENERAL_REQUIREMENTS = [
    "PyYAML",
    "requests",
    "beautifulsoup4"
]
requirements.InstallPackage(GENERAL_REQUIREMENTS)

import services_manager as servMgr
servMgr.InstallAllRequirements()