import os


class RepositoryPathHelper:
    """
    A helper class to adjust repository and params repository paths based on the owner.
    """

    def __init__(self, git_dir, owner="Utilities-tkgieng"):
        """
        Initialize the CommandHelper.

        Args:
          git_dir (str): The base directory containing git repositories.
          owner (str): The GitHub owner. Defaults to "Utilities-tkgieng".
        """
        self.git_dir = git_dir
        self.owner = owner

    def adjust_path(self, repo):
        """
        Adjusts the repository path.

        Args:
          repo (str): The repository name.

        Returns:
          tuple: Adjusted name and directory path.
        """
        repo, repo_dir = self._adjust_path(repo)

        if not os.path.isdir(repo_dir):
            raise ValueError(f"Could not find repo directory: {repo_dir}")

        return repo, repo_dir

    def adjust_paths(self, repo, params_repo):
        """
        Adjusts the repository and params repository paths.

        Args:
          repo (str): The repository name.
          params_repo (str): The params repository name.

        Returns:
          tuple: Adjusted repo, repo_dir, params_repo, and params_dir.
        """
        repo, repo_dir = self._adjust_path(repo)
        params_repo, params_dir = self._adjust_path(params_repo)

        if not os.path.isdir(repo_dir):
            raise ValueError(f"Could not find repo directory: {repo_dir}")
        if not os.path.isdir(params_dir):
            raise ValueError(f"Could not find params directory: {params_dir}")

        return repo, repo_dir, params_repo, params_dir

    def _adjust_path(self, name):
        """
        Adjusts a single path based on the owner.

        Args:
          name (str): The name of the repository or params repository.

        Returns:
          tuple: Adjusted name and directory path.
        """
        name_without_owner = None
        if name.endswith(self.owner):
            name_without_owner = name[: -len(self.owner) - 1]

        if name_without_owner:
            # name = name_without_owner
            dir_path = os.path.join(self.git_dir, name_without_owner)
        else:
            dir_path = os.path.join(self.git_dir, name)

        if self.owner != "Utilities-tkgieng":
            # name = f"{name}-{self.owner}"
            dir_path = os.path.join(self.git_dir, f"{name}-{self.owner}")

        return name, dir_path
