import Utilities.install_requirements as requirements

GENERAL_REQUIREMENTS = [
    "PyYAML",
    "requests",
    "beautifulsoup4",
    "tiktoken",
    "pydub",
    "websockets>=15.0.0,<16.0.0",
    "asyncio",
    "av",
    "cryptography",
    "ddgs"
]

def InstallRequirements() -> None:
    requirements.InstallPackage(GENERAL_REQUIREMENTS)

    import services_manager as servMgr
    servMgr.InstallAllRequirements()

if (__name__ == "__main__"):
    InstallRequirements()