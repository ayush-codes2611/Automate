# Phase B: LLM-based Automation Agent for DataWorks Solutions

# B1 & B2: Security Checks
import os
import re
import signal
from PIL import Image
import json
import requests
import subprocess
from datetime import datetime
# import whisper
import sqlite3
import duckdb
import pandas as pd
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
import markdown
from fastapi import FastAPI, HTTPException
from typing import Literal, Dict, Any




# def B12(filepath):
#     if filepath.startswith('/data'):
#         # raise PermissionError("Access outside /data is not allowed.")
#         # print("Access outside /data is not allowed.")
#         return True
#     else:
#         return False
    
# B1: Read a File
def B1(task_description: str):
    """Ensures the task does not access files outside /data and executes safely."""
    print(f"B1: within B1")

    def is_within_data_folder(path: str, base_folder: str = "/data") -> bool:
        """Ensures the path is within the /data directory."""
        abs_base = os.path.abspath(base_folder)
        abs_path = os.path.abspath(path)
        return abs_path.startswith(abs_base)

    def validate_task(task: str):
        """Validates that the task does not attempt to access files outside /data."""
        restricted_keywords = ["../", "/etc/", "/var/", "/home/", "/root/", "/usr/", "/proc/", "/sys/", "/dev/"]
        
        # Block explicit restricted paths
        if any(keyword in task for keyword in restricted_keywords):
            return {"error": "Access to files outside /data is not allowed."}

        # Detect absolute or relative file paths
        path_pattern = re.compile(r'(/\S+)|(\.\./\S*)')
        matches = path_pattern.findall(task)
        for match in matches:
            file_path = match[0] if match[0] else match[1]  # Pick the non-empty match
            if os.path.isabs(file_path) and not is_within_data_folder(file_path):
                return {"error": f"Access to {file_path} is denied."}

        return None  # Task is valid

    # Validate the task description
    validation_result = validate_task(task_description)
    if validation_result:
        return validation_result  # Return security error if found

    return {"message": "Task executed successfully."}

# B2: Write to a File
def B2(task_description: str):
    """Ensures that no file or directory is deleted anywhere in the system, even if explicitly requested."""

    def contains_delete_intent(task: str) -> bool:
        """Checks if the task contains any request to delete files or directories, anywhere in the system."""
        delete_patterns = [
            r"\bdelete\b", r"\bremove\b", r"\berase\b", r"\bdestroy\b", r"\bpurge\b",
            r"\btruncate\b", r"\bclean up\b", r"\bwipe\b", r"\bshred\b", r"\bexpunge\b",
            r"\brm\b", r"\brmdir\b", r"\bunlink\b", r"\bdel\b", r"\bfstrim\b"
        ]
        return any(re.search(pattern, task, re.IGNORECASE | re.MULTILINE) for pattern in delete_patterns)

    # Check for file deletion intent
    if contains_delete_intent(task_description):
        return {"error": "File deletion is strictly prohibited anywhere in the system."}

def get_data_folder():
    """Determine the correct data folder (either /data or the A1-created folder)."""
    data_folder = "/data"
    
    if not os.path.exists(data_folder):
        # Find where A1 created the folder
        potential_paths = ["/alternative_path1", "/alternative_path2"]  # Dynamically detect these
        for path in potential_paths:
            if os.path.exists(path):
                return path
                
        raise FileNotFoundError("Data folder not found. Ensure A1 has run successfully.")
    
    return data_folder

def fetch_and_save_api_data(api_url: str, output_filename: str, headers: dict = None):
    """
    Fetch data from an API and save it to a file.
    
    - Ensures the output file is within the data directory.
    - Handles errors and timeouts.
    """
    try:
        # Get the correct data folder
        data_folder = get_data_folder()
        
        # Ensure the output file is within the correct folder
        if not output_filename.startswith(data_folder):
            raise PermissionError("Attempt to save file outside the data directory is blocked.")

        # Fetch API data with a timeout
        response = requests.get(api_url, headers=headers or {}, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Save response data to the file
        output_path = os.path.join(data_folder, os.path.basename(output_filename))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, indent=4)
        
        return {"status": "success", "message": f"Data saved to {output_path}"}
    
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"API request failed: {str(e)}"}
    except PermissionError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# B3: Fetch data from an API and save it
def get_data_folder():
    """Determine the correct data folder (either /data or the A1-created folder)."""
    data_folder = "/data"

    if not os.path.exists(data_folder):
        # Find where A1 created the folder
        potential_paths = ["/alternative_path1", "/alternative_path2"]  # Detect dynamically
        for path in potential_paths:
            if os.path.exists(path):
                return path
                
        raise FileNotFoundError("Data folder not found. Ensure A1 has run successfully.")
    
    return data_folder

def B3(api_url: str, output_filename: str, headers: dict = None):
    """
    Fetch data from an API and save it within the /data directory.

    - Ensures the output file is within the /data directory.
    - Handles HTTP errors and exceptions safely.
    - Modifications to existing files inside /data are allowed.
    """
    try:
        # Get the correct data folder
        data_folder = get_data_folder()

        # Ensure the output file stays within /data
        if not output_filename.startswith(data_folder):
            raise PermissionError("Attempt to save file outside the /data directory is blocked.")

        # Full output path
        output_path = os.path.join(data_folder, os.path.basename(output_filename))

        # Fetch API data with a timeout
        response = requests.get(api_url, headers=headers or {}, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Read existing data if the file already exists
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        # Append new data
        new_data = response.json()
        if isinstance(existing_data, list) and isinstance(new_data, list):
            existing_data.extend(new_data)
        else:
            existing_data = new_data  # Replace only if it's not a list

        # Save updated data
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4)

        return {"status": "success", "message": f"Data saved to {output_path}"}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"API request failed: {str(e)}"}
    except PermissionError as e:
        return {"status": "error", "message": str(e)}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Failed to decode existing JSON file."}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


# B4: Clone a Git Repo and Make a Commit


def B4(repo_url, commit_message="Automated commit by the agent"):
    """Clones a Git repository into /data, makes a change, and commits it."""

    if not repo_url.endswith(".git"):
        return {"status": "error", "message": "Invalid repository URL."}

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    clone_path = f"/data/{repo_name}"

    # Ensure the repo is inside /data
    if not clone_path.startswith("/data/"):
        return {"status": "error", "message": "Cloning outside /data is not allowed."}

    try:
        # Clone the repository if not already cloned
        if not os.path.exists(clone_path):
            subprocess.run(["git", "clone", repo_url, clone_path], check=True)
        else:
            return {"status": "error", "message": "Repository already exists in /data."}

        # Modify a file (e.g., update timestamp)
        timestamp_file = os.path.join(clone_path, "timestamp.txt")
        with open(timestamp_file, "w") as file:
            file.write(f"Last modified: {datetime.utcnow()}")

        # Commit the change
        subprocess.run(["git", "-C", clone_path, "add", "."], check=True)
        subprocess.run(["git", "-C", clone_path, "commit", "-m", commit_message], check=True)

        return {"status": "success", "message": f"Repository cloned and committed: {clone_path}"}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Git operation failed: {e}"}
    
def B5(db_filename, query, output_filename):
    """Runs a SQL query on a SQLite or DuckDB database and saves the results to a CSV file."""
    
    # Ensure files are inside /data/
    if not (db_filename.startswith("/data/") and output_filename.startswith("/data/")):
        return {"status": "error", "message": "Database and output file must be inside /data/."}

    # Prevent destructive queries
    forbidden_keywords = ["DROP", "DELETE", "ALTER"]
    if any(kw in query.upper() for kw in forbidden_keywords):
        return {"status": "error", "message": "Destructive SQL statements are not allowed."}

    try:
        # Check database type
        if db_filename.endswith(".db"):
            conn = sqlite3.connect(db_filename)
        elif db_filename.endswith(".duckdb"):
            conn = duckdb.connect(db_filename)
        else:
            return {"status": "error", "message": "Unsupported database format."}

        # Run query
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Save result to CSV
        df.to_csv(output_filename, index=False)

        return {"status": "success", "message": f"Query results saved to {output_filename}"}

    except Exception as e:
        return {"status": "error", "message": f"SQL execution failed: {e}"}


# B5: Run SQL Query
# def B5(db_path, query, output_filename):
#     if not B12(db_path):
#         return None
#     import sqlite3, duckdb
#     conn = sqlite3.connect(db_path) if db_path.endswith('.db') else duckdb.connect(db_path)
#     cur = conn.cursor()
#     cur.execute(query)
#     result = cur.fetchall()
#     conn.close()
#     with open(output_filename, 'w') as file:
#         file.write(str(result))
#     return result
#B6 extract_website_data
def B6(url, data_type, output_filename):
    """Scrapes a website and saves extracted data to /data/"""
    
    # Ensure output file is inside /data/
    if not output_filename.startswith("/data/"):
        return {"status": "error", "message": "Output file must be inside /data/."}

    # Prevent scraping local/private networks
    if "localhost" in url or "127.0.0.1" in url or "internal" in url:
        return {"status": "error", "message": "Access to local/internal URLs is not allowed."}

    try:
        # Respect robots.txt
        robots_url = "/".join(url.split("/")[:3]) + "/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        if not rp.can_fetch("*", url):
            return {"status": "error", "message": "Scraping is blocked by robots.txt."}

        # Fetch page content
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract required data
        if data_type == "text":
            extracted_data = {"text": soup.get_text()}
        elif data_type == "links":
            extracted_data = {"links": [a["href"] for a in soup.find_all("a", href=True)]}
        elif data_type == "tables":
            tables = pd.read_html(response.text)
            extracted_data = {"tables": [table.to_dict(orient="records") for table in tables]}
        else:
            return {"status": "error", "message": "Invalid data_type."}

        # Save data to file
        if output_filename.endswith(".json"):
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4)
        elif output_filename.endswith(".csv") and data_type == "tables":
            pd.DataFrame(tables[0]).to_csv(output_filename, index=False)
        else:
            return {"status": "error", "message": "Invalid output format for the selected data type."}

        return {"status": "success", "message": f"Data saved to {output_filename}"}

    except Exception as e:
        return {"status": "error", "message": f"Scraping failed: {e}"}

# # B7: Image Processing
# def B7(image_path, output_path, resize=None):
#     from PIL import Image
#     if not B12(image_path):
#         return None
#     if not B12(output_path):
#         return None
#     img = Image.open(image_path)
#     if resize:
#         img = img.resize(resize)
#     img.save(output_path)

# B8: Audio Transcription

def B7(input_filename, output_filename, width=None, height=None, quality=75):
    """Compress or resize an image and save it to /data/"""

    # Ensure files are within /data/
    if not (input_filename.startswith("/data/") and output_filename.startswith("/data/")):
        return {"status": "error", "message": "Both input and output files must be inside /data/."}

    # Ensure file exists
    if not os.path.exists(input_filename):
        return {"status": "error", "message": "Input file does not exist."}

    try:
        # Open image
        with Image.open(input_filename) as img:
            # Convert to RGB to avoid mode issues
            img = img.convert("RGB")

            # Resize if width or height is provided
            if width or height:
                img = img.resize((width or img.width, height or img.height))

            # Save image with compression
            img.save(output_filename, quality=quality if input_filename.lower().endswith((".jpg", ".jpeg")) else None)

        return {"status": "success", "message": f"Image saved to {output_filename}"}

    except Exception as e:
        return {"status": "error", "message": f"Image processing failed: {e}"}
#B8 transcribe_audio


# def B8(input_filename, output_filename, model="whisper"):
#     """Transcribe an MP3 audio file and save the text to /data/"""
    
#     # Ensure files are within /data/
#     if not (input_filename.startswith("/data/") and output_filename.startswith("/data/")):
#         return {"status": "error", "message": "Both input and output files must be inside /data/."}
    
#     # Ensure file exists
#     if not os.path.exists(input_filename):
#         return {"status": "error", "message": "Input file does not exist."}

#     try:
#         # Whisper model for transcription
#         if model == "whisper":
#             model = whisper.load_model("base")
#             result = model.transcribe(input_filename)
#             text = result["text"]

#         # Vosk model for transcription
#         elif model == "vosk":
#             output_text = subprocess.run(
#                 ["vosk-transcriber", input_filename], capture_output=True, text=True
#             )
#             text = output_text.stdout.strip()

#         # Save transcript to file
#         with open(output_filename, "w", encoding="utf-8") as f:
#             f.write(text)

#         return {"status": "success", "message": f"Transcription saved to {output_filename}"}

#     except Exception as e:
#         return {"status": "error", "message": f"Transcription failed: {e}"}

    



    


# # B9: Markdown to HTML Conversion



def convert_markdown_to_html(input_filename, output_filename):
    """Convert a Markdown file to HTML and save the output inside /data/"""
    
    # Ensure files are within /data/
    if not (input_filename.startswith("/data/") and output_filename.startswith("/data/")):
        return {"status": "error", "message": "Both input and output files must be inside /data/."}

    # Ensure file exists
    if not os.path.exists(input_filename):
        return {"status": "error", "message": "Input file does not exist."}

    try:
        # Read the Markdown file
        with open(input_filename, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content)

        # Save the HTML output
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {"status": "success", "message": f"HTML conversion saved to {output_filename}"}

    except Exception as e:
        return {"status": "error", "message": f"Conversion failed: {e}"}

#B10 filter_csv

def B10(csv_filename: str, column_name: str, filter_value: str, 
        comparison_operator: Literal["=", "!=", ">", "<", ">=", "<="] = "=") -> Dict[str, Any]:
    """
    B10: Filter a CSV file inside /data/ based on a column value and return JSON data.

    Args:
    - csv_filename (str): Path to the CSV file inside `/data/`.
    - column_name (str): The column to filter.
    - filter_value (str): The value to match in the specified column.
    - comparison_operator (str): The operator for filtering (default: '=').

    Returns:
    - Dict[str, Any]: JSON response containing filtered rows or an error message.
    """

    # Ensure the CSV file is within the `/data/` directory
    if not csv_filename.startswith("/data/"):
        return {"status": "error", "detail": "Access restricted to /data/."}

    # Check if the file exists
    if not os.path.exists(csv_filename):
        return {"status": "error", "detail": "CSV file not found."}

    try:
        # Read CSV file
        df = pd.read_csv(csv_filename)

        # Ensure the specified column exists
        if column_name not in df.columns:
            return {"status": "error", "detail": "Column not found in CSV."}

        # Convert filter_value to the column's data type
        try:
            col_type = df[column_name].dtype
            if pd.api.types.is_numeric_dtype(col_type):
                filter_value = float(filter_value)
            elif pd.api.types.is_datetime64_any_dtype(col_type):
                filter_value = pd.to_datetime(filter_value)
        except ValueError:
            return {"status": "error", "detail": "Invalid filter value format."}

        # Apply filtering based on the comparison operator
        if comparison_operator == "=":
            filtered_df = df[df[column_name] == filter_value]
        elif comparison_operator == "!=":
            filtered_df = df[df[column_name] != filter_value]
        elif comparison_operator == ">":
            filtered_df = df[df[column_name] > filter_value]
        elif comparison_operator == "<":
            filtered_df = df[df[column_name] < filter_value]
        elif comparison_operator == ">=":
            filtered_df = df[df[column_name] >= filter_value]
        elif comparison_operator == "<=":
            filtered_df = df[df[column_name] <= filter_value]

        # Convert to JSON
        return {"status": "success", "data": filtered_df.to_dict(orient="records")}

    except Exception as e:
        return {"status": "error", "detail": f"Filtering failed: {e}"}


