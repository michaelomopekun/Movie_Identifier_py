import os
from pathlib import Path


class EnvManager:

    def update_env_variable(self, key, value, env_file_path=None):

        if env_file_path is None:
            env_file_path = Path(__file__).resolve().parent.parent / ".env"

        lines = []

        found = False

        with open(env_file_path, "r") as file:
            for line in file:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True

                else:
                    lines.append(line)

        if not found:
            lines.append(f"{key}={value}\n")

        with open(env_file_path, "w") as file:
            file.writelines(lines)

        os.environ[key] = str(value)

envManager = EnvManager()
