from data.base import BaseData

class GitHubUsers(BaseData):
    """Mocked GitHub users data source."""

    def __init__(self):
        super().__init__(name="github_users", description="Mocked GitHub users data source.")

    @property
    def data(self) -> dict:
        return {
            "octocat": {
                "login": "octocat",
                "name": "The Octocat",
                "email": "octocat@github.com",
                "bio": "GitHub mascot and git guru",
                "public_repos": 8,
                "followers": 9432,
                "following": 9,
                "created_at": "2011-01-25T18:44:36Z",
                "location": "San Francisco",
                "company": "@github"
            },
            "torvalds": {
                "login": "torvalds",
                "name": "Linus Torvalds",
                "email": "torvalds@linux-foundation.org",
                "bio": "Creator of Linux and Git",
                "public_repos": 6,
                "followers": 182500,
                "following": 0,
                "created_at": "2011-09-03T15:26:22Z",
                "location": "Portland, OR",
                "company": "Linux Foundation"
            },
            "testuser": {
                "login": "testuser",
                "name": "Test User",
                "email": "test@example.com",
                "bio": "Software developer and open source enthusiast",
                "public_repos": 42,
                "followers": 156,
                "following": 89,
                "created_at": "2015-03-12T10:00:00Z",
                "location": "Milan, Italy",
                "company": "Tech Corp"
            }
        }
    
class GitHubRepos(BaseData):
    """Mocked GitHub repositories data source."""

    def __init__(self):
        super().__init__(name="github_repos", description="Mocked GitHub repositories data source.")

    @property
    def data(self) -> dict:
        return {
            "octocat": [
                {"name": "hello-world", "description": "My first repository on GitHub!", "language": "Ruby", "stars": 1500},
                {"name": "Spoon-Knife", "description": "This repo is for demonstration purposes only.", "language": "HTML", "stars": 1000}
            ],
            "torvalds": [
                {"name": "linux", "description": "Linux kernel source tree", "language": "C", "stars": 150000},
                {"name": "subsurface", "description": "Dive log software", "language": "C++", "stars": 3500}
            ],
            "testuser": [
                {"name": "awesome-project", "description": "An awesome project that does amazing things.", "language": "Python", "stars": 250},
                {"name": "data-analyzer", "description": "A tool for analyzing data efficiently.", "language": "JavaScript", "stars": 300}
            ]
        }