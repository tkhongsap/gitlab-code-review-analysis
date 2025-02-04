#!/usr/bin/env python3
import requests
import base64
import urllib.parse
import os
import re
from dotenv import load_dotenv
from colorama import init, Fore, Style
from datetime import datetime

# Initialize colorama for cross-platform color support
init()

load_dotenv(True)

# ---------------------------
# Configuration
# ---------------------------
BASE_URL = "https://gitlabii.thaibevapp.com/api/v4"
ROOT_GROUP = "gitlab-code-review"
PRIVATE_TOKEN = os.getenv("GITLAB_API_KEY")
headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
LOCAL_BASE = "docs"

def log_info(message):
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message):
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_file_download(filepath):
    # Split the path into directory and filename
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Downloaded to:")
    print(f"  {Fore.BLUE}Directory:{Style.RESET_ALL} {directory}")
    print(f"  {Fore.BLUE}File:{Style.RESET_ALL} {filename}")

def log_warning(message):
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_error(message):
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def process_project(project, project_num, total_projects):
    """
    Process a single project and download its markdown files.
    """
    project_name = project['path_with_namespace']
    log_info(f"\n[Project {project_num}/{total_projects}] Processing: {Fore.BLUE}{project_name}{Style.RESET_ALL}")
    project_id = project["id"]
    
    parts = project["path_with_namespace"].split("/")
    local_project_dir = os.path.join(LOCAL_BASE, *[sanitize_filename(p) for p in parts])
    os.makedirs(local_project_dir, exist_ok=True)
    
    tree_url = f"{BASE_URL}/projects/{project_id}/repository/tree"
    tree_params = {
        "path": "code-review-scores",
        "per_page": 100
    }
    response_tree = requests.get(tree_url, headers=headers, params=tree_params)
    if response_tree.status_code != 200:
        log_warning(f"No 'code-review-scores' folder found in project")
        return 0
    
    files = response_tree.json()
    md_files = [f for f in files if f["type"] == "blob" and f["name"].endswith(".md")]
    
    if not md_files:
        log_warning("No markdown files found")
        return 0
    
    log_info(f"Found {len(md_files)} markdown files to process")
    files_downloaded = 0
    
    for idx, file in enumerate(md_files, 1):
        print(f"\n{Fore.CYAN}[{idx}/{len(md_files)}]{Style.RESET_ALL} Processing file: {file['name']}")
        
        path_parts = file["path"].split("/")
        sanitized_parts = [sanitize_filename(part) for part in path_parts]
        relative_file_path = os.path.join(*sanitized_parts)
        file_local_path = os.path.join(local_project_dir, relative_file_path)
        os.makedirs(os.path.dirname(file_local_path), exist_ok=True)
        
        encoded_file_path = urllib.parse.quote(file["path"], safe='')
        file_endpoint = f"{BASE_URL}/projects/{project_id}/repository/files/{encoded_file_path}"
        file_params = {"ref": "master"}
        response_file = requests.get(file_endpoint, headers=headers, params=file_params)
        
        if response_file.status_code == 200:
            file_data = response_file.json()
            content_encoded = file_data["content"]
            content_bytes = base64.b64decode(content_encoded)
            content_text = content_bytes.decode("utf-8")
            with open(file_local_path, "w", encoding="utf-8") as f:
                f.write(content_text)
            log_file_download(file_local_path)
            files_downloaded += 1
        else:
            log_error(f"Failed to download: {response_file.text}")
    
    return files_downloaded

def main():
    start_time = datetime.now()
    print(f"\n{Fore.CYAN}=== GitLab Code Review Analysis Tool ==={Style.RESET_ALL}")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    base_group_dir = os.path.join(LOCAL_BASE, ROOT_GROUP)
    os.makedirs(base_group_dir, exist_ok=True)
    log_info(f"Base directory: {base_group_dir}")
    
    encoded_group = urllib.parse.quote(ROOT_GROUP, safe='')
    group_info_url = f"{BASE_URL}/groups/{encoded_group}"
    response_group = requests.get(group_info_url, headers=headers)
    if response_group.status_code != 200:
        log_error(f"Failed to get root group info: {response_group.text}")
        exit(1)
    
    group_info = response_group.json()
    group_id = group_info["id"]
    log_success(f"Connected to group: {group_info['name']} (ID: {group_id})")
    
    projects_url = f"{BASE_URL}/groups/{group_id}/projects"
    projects_params = {"include_subgroups": True, "per_page": 100}
    response_projects = requests.get(projects_url, headers=headers, params=projects_params)
    if response_projects.status_code != 200:
        log_error(f"Failed to get projects: {response_projects.text}")
        exit(1)
    
    projects = response_projects.json()
    total_projects = len(projects)
    log_info(f"Found {total_projects} projects to process")
    
    total_files_downloaded = 0
    for idx, project in enumerate(projects, 1):
        files_downloaded = process_project(project, idx, total_projects)
        total_files_downloaded += files_downloaded
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{Fore.CYAN}=== Summary ==={Style.RESET_ALL}")
    print(f"Total projects processed: {total_projects}")
    print(f"Total files downloaded: {total_files_downloaded}")
    print(f"Duration: {duration.total_seconds():.2f} seconds")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()