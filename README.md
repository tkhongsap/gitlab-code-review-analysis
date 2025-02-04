# GitLab Code Review Analysis

A Python tool to extract and analyze code review files from GitLab repositories. This tool traverses through GitLab groups and projects, downloading markdown files from `code-review-scores` directories while maintaining the original GitLab folder structure locally.

## Features

- Recursively traverses GitLab groups and subgroups
- Downloads markdown files from `code-review-scores` directories
- Maintains original GitLab folder structure locally
- Colored terminal output for better visibility
- Progress tracking for downloads
- Execution summary with timing information

## Project Structure

```
gitlab-code-review-analysis/
├── 01-extract-code-review.py    # Main extraction script
├── .env                         # Environment variables (GitLab token)
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
└── docs/                        # Downloaded files directory
    └── gitlab-code-review/      # Root group directory
        └── otc/                 # Subgroup
            └── sapmiddleware/   # Project
                └── code-review-scores/  # Review files
```

## Prerequisites

- Python 3.x
- GitLab API access token with the following permissions:
  - `read_api` - For accessing the GitLab API
  - `read_repository` - For reading repository content

## Installation

1. Clone the repository:

```

## Environment Variables

The following environment variables are required:

```bash
GITLAB_API_KEY=your_gitlab_token_here  # Your GitLab personal access token
```

You can set these by either:
- Creating a `.env` file in the project root
- Setting them in your system environment
- Setting them in your CI/CD pipeline
```

## Troubleshooting

Common issues and solutions:

- **Authentication Failed**: Ensure your GitLab token is valid and has the required permissions
- **No Files Found**: Verify that the project has a `code-review-scores` directory
- **Connection Error**: Check your network connection and GitLab API URL