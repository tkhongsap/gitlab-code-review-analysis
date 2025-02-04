#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()

def log_info(message):
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message):
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_warning(message):
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_error(message):
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def extract_scores(content):
    """Extract scores from markdown content."""
    scores = {
        "Correctness and Functionality": None,
        "Code Quality and Maintainability": None,
        "Performance and Efficiency": None,
        "Security and Vulnerability Assessment": None,
        "Code Consistency and Style": None,
        "Scalability and Extensibility": None,
        "Error Handling and Robustness": None
    }
    
    # Regular expression to match score lines
    score_pattern = r"(\d+)/10"
    
    lines = content.split('\n')
    current_category = None
    
    for line in lines:
        # Check if line contains any of our categories
        for category in scores.keys():
            if category in line:
                current_category = category
                # Try to find score in this line
                match = re.search(score_pattern, line)
                if match:
                    scores[category] = int(match.group(1))
                break
        
        # If we're in a category and haven't found a score yet, check next line
        if current_category and scores[current_category] is None:
            match = re.search(score_pattern, line)
            if match:
                scores[current_category] = int(match.group(1))
                current_category = None
    
    return scores

def extract_additional_fields(content):
    """Extract additional fields: overall score and key improvement items from markdown content."""
    overall_score = None
    key_improvement_items = []
    
    lines = content.split('\n')
    in_improvements = False
    for line in lines:
        if "Overall Score:" in line:
            parts = line.split("Overall Score:")
            if len(parts) > 1:
                overall_score = parts[1].strip()
        elif "Key Improvement Items:" in line:
            in_improvements = True
            continue
        elif in_improvements:
            # End the improvement section if an empty line or a new header is encountered.
            if line.strip() == "" or line.lstrip().startswith("#"):
                in_improvements = False
            else:
                # Match bullet items starting with "1. " or "- "
                match = re.match(r"^\s*(?:\d+\.\s*|\-\s*)(.*)", line)
                if match:
                    item = match.group(1).strip()
                    key_improvement_items.append(item)
                else:
                    key_improvement_items.append(line.strip())
    return overall_score, key_improvement_items

def extract_all_data(content):
    """Extract all markdown data points: headers and their content.
    
    This function uses a simple heuristic to collect text under each header.
    Headers (lines starting with '#' up to '######') become keys and their 
    following lines (until the next header) become values.
    """
    data = {}
    header_pattern = re.compile(r"^(#{1,6})\s+(.*)")
    current_header = None
    # We'll also capture any content before the first header under the key 'main'
    data["main"] = ""
    
    for line in content.splitlines():
        match = header_pattern.match(line)
        if match:
            # If a new header is found, update current_header and initialize its value.
            current_header = match.group(2).strip()
            data[current_header] = ""  # Initialize empty string for header content.
        else:
            if current_header:
                # Append current line to the current header key.
                data[current_header] += line + "\n"
            else:
                # Append to main if no header encountered yet.
                data["main"] += line + "\n"
    return data

def process_markdown_files(base_dir="docs/gitlab-code-review"):
    """Process all markdown files and extract scores."""
    start_time = datetime.now()
    log_info(f"\n=== Starting Score Extraction ===")
    log_info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create extracted_scores directory
    extracted_dir = base_dir.replace("gitlab-code-review", "extracted_scores")
    files_processed = 0
    
    # Walk through the directory structure
    for root, dirs, files in os.walk(base_dir):
        # Skip if no markdown files
        md_files = [f for f in files if f.endswith('.md')]
        if not md_files:
            continue
        
        # Create corresponding directory in extracted_scores, maintaining the same relative structure.
        # This replaces "gitlab-code-review" in the path with "extracted_scores"
        output_dir = root.replace("gitlab-code-review", "extracted_scores")
        os.makedirs(output_dir, exist_ok=True)
        
        log_info(f"Processing directory: {root}")
        
        # Process each markdown file
        for md_file in md_files:
            md_path = os.path.join(root, md_file)
            log_info(f"\nProcessing file: {md_file}")
            
            try:
                # Read markdown content
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract scores
                scores = extract_scores(content)
                
                # Extract additional fields from the markdown content.
                overall, improvements = extract_additional_fields(content)
                scores["Overall Score"] = overall if overall else "N/A"
                scores["Key Improvement Items"] = improvements
                
                # Optionally, extract all data points from the markdown.
                # This will parse all headers and their associated content.
                full_data = extract_all_data(content)
                scores["Full Markdown Data"] = full_data
                
                # Create JSON filename (replace .md with .json)
                json_filename = os.path.splitext(md_file)[0] + '.json'
                json_path = os.path.join(output_dir, json_filename)
                
                # Save scores to JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(scores, f, indent=2)
                
                log_success(f"Extracted scores saved to: {json_path}")
                files_processed += 1
                
            except Exception as e:
                log_error(f"Error processing {md_file}: {str(e)}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{Fore.CYAN}=== Summary ==={Style.RESET_ALL}")
    print(f"Total files processed: {files_processed}")
    print(f"Duration: {duration.total_seconds():.2f} seconds")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Calculate average scores from all JSON files in the extracted_scores directory.
    avg_scores = calculate_average_scores()
    save_average_scores(avg_scores)

def calculate_average_scores(base_dir="docs/extracted_scores"):
    """Calculate average scores from all JSON files in the extracted_scores directory."""
    metrics = [
        "Correctness and Functionality",
        "Code Quality and Maintainability",
        "Performance and Efficiency",
        "Security and Vulnerability Assessment",
        "Code Consistency and Style",
        "Scalability and Extensibility",
        "Error Handling and Robustness",
        "Overall Score"
    ]
    sum_dict = {metric: 0.0 for metric in metrics}
    count_dict = {metric: 0 for metric in metrics}
    
    # Track unique projects
    projects_set = set()
    total_files = 0
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith('.json'):
                total_files += 1
                # Extract project path from the file path
                # Example: docs/extracted_scores/otc/sapmiddleware/... -> otc/sapmiddleware
                project_path = os.path.relpath(root, base_dir).split('code-review-scores')[0].strip('/')
                if project_path:  # Only add if it's not empty
                    projects_set.add(project_path)
                
                json_path = os.path.join(root, f)
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    for metric in metrics:
                        value = data.get(metric)
                        if value is None:
                            continue
                        if metric == "Overall Score":
                            # Expecting a string like "7.14/10"; otherwise, try a numeric value.
                            if isinstance(value, str) and "/" in value:
                                try:
                                    score_val = float(value.split("/")[0].strip())
                                    sum_dict[metric] += score_val
                                    count_dict[metric] += 1
                                except Exception:
                                    pass
                            elif isinstance(value, (int, float)):
                                sum_dict[metric] += float(value)
                                count_dict[metric] += 1
                        else:
                            if isinstance(value, (int, float)):
                                sum_dict[metric] += float(value)
                                count_dict[metric] += 1
                except Exception as e:
                    log_error(f"Error reading {json_path}: {e}")
                    
    avg_results = {}
    for metric in metrics:
        if count_dict[metric] > 0:
            avg_results[metric] = round(sum_dict[metric] / count_dict[metric], 2)
        else:
            avg_results[metric] = "N/A"
    
    # Add metadata about the analysis
    avg_results["Metadata"] = {
        "Total Files Processed": total_files,
        "Total Projects": len(projects_set),
        "Projects List": sorted(list(projects_set))
    }
    return avg_results

def save_average_scores(avg_dict, base_dir="docs/extracted_scores"):
    """Save the average scores as a JSON file in the extracted_scores directory."""
    output_path = os.path.join(base_dir, "summary_average_scores.json")
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(avg_dict, outfile, indent=2)
        log_success(f"Average scores saved to: {output_path}")
    except Exception as e:
        log_error(f"Error saving average scores: {e}")

if __name__ == "__main__":
    process_markdown_files()
