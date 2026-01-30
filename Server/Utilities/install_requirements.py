import subprocess
import os
import copy
import Utilities.logs as logs
import exceptions

PIP_COMMANDS = ["pip", "pip3" "python -m pip", "python3 -m pip"]
INSTALL_PIP_COMMANDS = ["python -m ensurepip", "python3 -m ensurepip"]

def GetPIPCommand(InstallIfNotFound: bool = True) -> str | None:
    """
    Get automatically the PIP command.

    Args:
        InstallIfNotFound (bool): Install PIP if the command could not be found.
    
    Returns:
        str | None
    """
    for command in PIP_COMMANDS:
        logs.WriteLog(logs.INFO, f"[requirements_installation] Testing PIP command `{command}`...")
        process = subprocess.run(command.split(" ") + ["--help"], text = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        
        if (process.returncode == 0):
            logs.WriteLog(logs.INFO, f"[requirements_installation] Got PIP command `{command}`!")
            return command
    
    logs.WriteLog(logs.ERROR, "[requirements_installation] Could not find PIP command automatically.")

    if (InstallIfNotFound):
        InstallPIP()
        return GetPIPCommand(False)

def InstallPIP() -> None:
    """
    Install PIP automatically.

    Returns:
        None
    """
    for command in INSTALL_PIP_COMMANDS:
        logs.WriteLog(logs.INFO, f"[requirements_installation] Trying to install PIP with the command `{command}`...")
        process = subprocess.run(command.split(" "))

        if (process.returncode == 0):
            logs.WriteLog(logs.INFO, f"[requirements_installation] PIP installed with the command `{command}`!")
            return
    
    logs.WriteLog(logs.ERROR, "[requirements_installation] Could not install PIP automatically.")
    raise exceptions.InstallationError("Could not get PIP install command automatically.")

def InstallPackage(
        Packages: list[str],
        PIPCommand: str | None = None,
        EnvVars: dict[str, str | int | float] = {},
        PIPOptions: list[str] = []
    ) -> None:
    """
    Install a PIP package.

    Args:
        Packages (list[str]): Packages to install.
        PIPCommand (str | None): PIP command to use. If `None` it will be set automatically.
        EnvVars (dict[str, str | int | float]): Environment variables.
        PIPOptions (list[str]): PIP options. Example: `--upgrade`.
    
    Returns:
        None
    """
    if (PIPCommand is None):
        logs.WriteLog(logs.INFO, "[requirements_installation] PIP command is None. Trying to get automatically.")
        PIPCommand = GetPIPCommand(True)

        if (PIPCommand is None):
            logs.WriteLog(logs.ERROR, "[requirements_installation] Could not get PIP command automatically.")
            raise exceptions.InstallationError("Could not get PIP command automatically.")
    
    cmd = PIPCommand.split(" ") + ["install"] + PIPOptions + Packages
    env = copy.deepcopy(os.environ)

    for name, value in EnvVars.items():
        env[name] = value

    logs.WriteLog(logs.INFO, f"[requirements_installation] Executing installation command `{cmd}`...")
    process = subprocess.run(cmd, env = env, stderr = subprocess.PIPE)

    if (process.returncode != 0):
        logs.WriteLog(logs.ERROR, f"[requirements_installation] Error executing installation command:\n```plaintext\n{process.stderr.decode('utf-8')}\n```")
        raise exceptions.InstallationError(f"Error executing installation command:\n```plaintext\n{process.stderr.decode('utf-8')}\n```")
    
    logs.WriteLog(logs.INFO, "[requirements_installation] Package installed!")