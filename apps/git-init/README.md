# Initialize Git Repo

Select an existing folder and this tool will run `git init`, rename the default branch to `main`, and create empty `README.md` and `.gitignore` files.

## Usage

1. Launch the tool and browse to the project folder you want under version control.
2. A terminal window confirms each step (init, branch rename, file creation).
3. Begin committing work immediately—stage the generated files or replace them with richer content.

## Notes

- Existing Git repositories are left untouched; the script will still run but `git init` reports the directory is already initialised.
- Update the generated `.gitignore` with project-specific patterns after the initial commit.
