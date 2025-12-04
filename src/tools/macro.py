from tools.base import BaseTool
from data.github import GitHubUsers, GitHubRepos

class ExtractGitHubProfile(BaseTool):
    """Tool to extract GitHub profile information from a username."""

    def __init__(self):
        super().__init__(
            name="extract_github_profile", 
            description="Extract GitHub profile information from a username.", 
            parameters={
                "username": {
                    "type": str.__name__,
                    "description": "The GitHub username to extract profile information for.",
                    "required": True
                }
            },
            results={
                "profile": {
                    "type": dict.__name__,
                    "description": "The GitHub user's profile information."
                }
            }
        )

    def run(self, username: str) -> dict:
        users = GitHubUsers().data
        if username in users:
            user = users[username].copy()
            return user
        else:
            raise ValueError(f"Username '{username}' not found in mocked data.")

class ExtractGitHubRepo(BaseTool):
    """Tool to extract GitHub repository information from a username."""

    def __init__(self):
        super().__init__(
            name="extract_github_repo", 
            description="Extract all GitHub repositories information from a username.",
            parameters={
                "username": {
                    "type": str.__name__,
                    "description": "The GitHub username to extract repository information for.",
                    "required": True
                }
            },
            results={
                "repositories": {
                    "type": list.__name__,
                    "description": "The list of GitHub repositories for the user."
                }
            }
        )

    def run(self, username: str) -> list:
        repos = GitHubRepos().data
        if username in repos:
            user_repos = repos[username].copy()
            return user_repos
        else:
            raise ValueError(f"Username '{username}' not found in mocked data.")
        
MACRO_TOOLS = [
    ExtractGitHubProfile,
    ExtractGitHubRepo
]