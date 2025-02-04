#!/usr/bin/env python3
import requests
import base64
import urllib.parse
import os
import re  # For sanitizing file and folder names
from dotenv import load_dotenv

load_dotenv(True)

# ---------------------------
# Configuration
# ---------------------------
BASE_URL = "https://gitlabii.thaibevapp.com/api/v4"
ROOT_GROUP = "gitlab-code-review"   # Starting GitLab group
PRIVATE_TOKEN = os.getenv("GITLAB_API_KEY")
headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}

# Local base directory where the files will be saved.
# The structure will be: docs/gitlab-code-review/...
LOCAL_BASE = "docs"

def sanitize_filename(filename):
    # Replace invalid Windows filename characters with an underscore
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def process_project(project):
    """
    For a given project, try to list markdown files under the "code-review-scores" directory.
    Local paths mirror the project's full path.
    """
    print(f"Processing project: {project['path_with_namespace']}")
    project_id = project["id"]
    
    # Compute the local project directory based on the project's full path.
    # For example, if project["path_with_namespace"] is
    # "gitlab-code-review/otc/sapmiddleware", then the local directory will be:
    # "docs/gitlab-code-review/otc/sapmiddleware"
    parts = project["path_with_namespace"].split("/")
    # Sanitize each part to handle any invalid characters
    local_project_dir = os.path.join(LOCAL_BASE, *[sanitize_filename(p) for p in parts])
    os.makedirs(local_project_dir, exist_ok=True)
    
    # Look for markdown files in the "code-review-scores" directory of the repository.
    tree_url = f"{BASE_URL}/projects/{project_id}/repository/tree"
    tree_params = {
        "path": "code-review-scores",
        "per_page": 100  # adjust if needed
    }
    response_tree = requests.get(tree_url, headers=headers, params=tree_params)
    if response_tree.status_code != 200:
        print(f"No 'code-review-scores' folder in project {project['name']}: {response_tree.text}")
        return
    files = response_tree.json()
    
    # Filter for markdown files (those with .md extension)
    md_files = [f for f in files if f["type"] == "blob" and f["name"].endswith(".md")]
    if not md_files:
        print(f"No markdown files found in project {project['name']}")
        return
    
    for file in md_files:
        # The file["path"] is relative in the repo (e.g., "code-review-scores/README.md").
        # We want to mirror this folder structure within the local project directory.
        path_parts = file["path"].split("/")
        sanitized_parts = [sanitize_filename(part) for part in path_parts]
        relative_file_path = os.path.join(*sanitized_parts)
        file_local_path = os.path.join(local_project_dir, relative_file_path)
        os.makedirs(os.path.dirname(file_local_path), exist_ok=True)
        
        # Download the file content.
        encoded_file_path = urllib.parse.quote(file["path"], safe='')
        file_endpoint = f"{BASE_URL}/projects/{project_id}/repository/files/{encoded_file_path}"
        file_params = {"ref": "master"}  # Adjust branch if necessary.
        response_file = requests.get(file_endpoint, headers=headers, params=file_params)
        if response_file.status_code == 200:
            file_data = response_file.json()
            content_encoded = file_data["content"]
            content_bytes = base64.b64decode(content_encoded)
            content_text = content_bytes.decode("utf-8")
            with open(file_local_path, "w", encoding="utf-8") as f:
                f.write(content_text)
            print(f"Downloaded {file['name']} to {file_local_path}")
        else:
            print(f"Failed to download {file['name']} from project {project['name']}: {response_file.text}")

def main():
    # Retrieve root group info to get the group id.
    encoded_group = urllib.parse.quote(ROOT_GROUP, safe='')
    group_info_url = f"{BASE_URL}/groups/{encoded_group}"
    response_group = requests.get(group_info_url, headers=headers)
    if response_group.status_code != 200:
        print("Failed to get root group info:", response_group.text)
        exit(1)
    group_info = response_group.json()
    group_id = group_info["id"]
    print(f"Root group ID: {group_id}")
    
    # Get all projects under the specified group, including subgroups.
    projects_url = f"{BASE_URL}/groups/{group_id}/projects"
    projects_params = {"include_subgroups": True, "per_page": 100}
    response_projects = requests.get(projects_url, headers=headers, params=projects_params)
    if response_projects.status_code != 200:
        print("Failed to get projects:", response_projects.text)
        exit(1)
    projects = response_projects.json()
    print(f"Found {len(projects)} projects under {ROOT_GROUP}")
    
    for project in projects:
        process_project(project)

if __name__ == "__main__":
    main()