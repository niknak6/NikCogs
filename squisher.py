import os
import subprocess

def get_repo_path():
    try:
        # Get the current working directory
        cwd = os.getcwd()

        # Search for the root of the Git repository
        while not os.path.exists(os.path.join(cwd, ".git")):
            cwd = os.path.dirname(cwd)

        return cwd
    except Exception as e:
        print(f"Error finding repository path: {e}")
        return None

def squash_all_commits():
    repo_path = get_repo_path()
    if not repo_path:
        print("Repository path not found. Make sure you're inside a Git repository.")
        return

    try:
        # Change directory to the repository path
        os.chdir(repo_path)

        # Get the commit hash of the root commit (initial commit)
        root_commit_hash = subprocess.check_output(["git", "rev-list", "--max-parents=0", "HEAD"]).decode().strip()

        # Reset the branch to the root commit
        subprocess.run(["git", "reset", "--soft", root_commit_hash])

        # Commit all changes as a single commit
        subprocess.run(["git", "commit", "-m", "Squash all commits into one"])

        print("All commits squashed into a single commit. Remember to force-push if needed.")
    except Exception as e:
        print(f"Error squashing commits: {e}")

if __name__ == "__main__":
    squash_all_commits()
