import os

class CommandHelper:
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

      def adjust_repo_and_params_paths(self, repo, params_repo):
          """
          Adjusts the repository and params repository paths based on the owner.

          Args:
              repo (str): The repository name.
              params_repo (str): The params repository name.

          Returns:
              tuple: Adjusted repo, repo_dir, params_repo, and params_dir.
          """
          # Check if repo ends with the owner
          repo_without_owner = None
          if repo.endswith(self.owner):
              repo_without_owner = repo[: -len(self.owner) - 1]

          if repo_without_owner:
              repo = repo_without_owner
              repo_dir = os.path.join(self.git_dir, repo)
          else:
              repo_dir = os.path.join(self.git_dir, repo)

          # Check if params_repo ends with the owner
          params_repo_without_owner = None
          if params_repo.endswith(self.owner):
              params_repo_without_owner = params_repo[: -len(self.owner) - 1]

          if params_repo_without_owner:
              params_repo = params_repo_without_owner
              params_dir = os.path.join(self.git_dir, params_repo)
          else:
              params_dir = os.path.join(self.git_dir, params_repo)

          # Check if owner is not the default
          if self.owner != "Utilities-tkgieng":
              if repo_without_owner:
                  repo = f"{repo}-{self.owner}"
                  repo_dir = os.path.join(self.git_dir, repo)
              if params_repo_without_owner:
                  params_repo = f"{params_repo}-{self.owner}"
                  params_dir = os.path.join(self.git_dir, params_repo)

          if not os.path.isdir(repo_dir):
              raise ValueError(f"Could not find repo directory: {repo_dir}")
          if not os.path.isdir(params_dir):
              raise ValueError(f"Could not find params directory: {params_dir}")

          return repo, repo_dir, params_repo, params_dir

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
          name = name_without_owner
          dir_path = os.path.join(self.git_dir, name)
        else:
          dir_path = os.path.join(self.git_dir, name)

        if self.owner != "Utilities-tkgieng" and name_without_owner:
          name = f"{name}-{self.owner}"
          dir_path = os.path.join(self.git_dir, name)

        return name, dir_path
