# Create Virtualenv

Prompts for a target directory and optional virtualenv name, then runs `python3 -m venv` and upgrades pip. Ideal for quickly provisioning an isolated interpreter before installing project-specific dependencies.

## Usage

1. Launch the tool and select the folder where the environment should live (existing projects are fine).
2. Provide a name for the virtualenv directory or keep the default `.venv`.
3. A terminal window appears and executes the setup. Close it when the command finishes.

## Notes

- No additional packages are installed—activate the environment later and `pip install` what you need.
- Re-running with the same target/venv name will reuse the folder; delete it manually to start fresh.
