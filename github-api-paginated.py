import requests
import re
import json
import csv
from datetime import datetime
import os
import time

class GitHubRateLimitError(Exception):
    """Custom exception for GitHub rate limit errors"""
    pass

def get_github_token():
    """
    Retrieve GitHub token from environment variable or prompt user
    """
    # Try to get token from environment variable first
    token = os.environ.get('GITHUB_TOKEN')
    
    if not token:
        # Prompt user if no environment variable is set
        token = input("Please enter your GitHub Personal Access Token: ")
    
    return token

def parse_data(data):
    # If the data is an array, return that
    if isinstance(data, list):
        return data
    
    # Some endpoints respond with None instead of empty array
    # when there is no data. In that case, return an empty array.
    if not data:
        return []
    
    # Otherwise, the array of items that we want is in an object
    # Delete keys that don't include the array of items
    data = data.copy()
    data.pop('incomplete_results', None)
    data.pop('repository_selection', None)
    data.pop('total_count', None)
    
    # Pull out the array of items
    namespace_key = list(data.keys())[0]
    data = data[namespace_key]
    
    return data

def check_rate_limit(response):
    """
    Check and handle GitHub API rate limits
    """
    # Check if rate limit headers exist
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    
    if remaining == 0:
        # Calculate wait time
        current_time = int(time.time())
        wait_time = max(reset_time - current_time + 1, 0)
        
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
        time.sleep(wait_time)
        
        raise GitHubRateLimitError("Rate limit reached. Waiting to retry.")

def get_paginated_data(url, token=None, max_retries=3):
    # Next page link pattern
    next_pattern = re.compile(r'(?<=<)([\S]*)(?=>; rel="next")', re.IGNORECASE)
    
    # Ensure token is provided
    if not token:
        token = get_github_token()
    
    # Headers for GitHub API
    headers = {
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}"
    }
    
    pages_remaining = True
    data = []
    retries = 0
    
    while pages_remaining and retries < max_retries:
        try:
            # Make the request
            response = requests.get(
                url, 
                headers=headers, 
                params={"per_page": 100}
            )
            
            # Check for rate limiting
            if response.status_code == 403:
                try:
                    check_rate_limit(response)
                except GitHubRateLimitError:
                    continue
            
            # Detailed error handling
            if response.status_code == 403:
                print("Error 403: Forbidden. Possible reasons:")
                print("1. Insufficient permissions")
                print("2. Invalid or expired token")
                print("3. Rate limit exceeded")
                print(f"Response headers: {response.headers}")
                print(f"Response content: {response.text}")
                raise requests.exceptions.HTTPError("Access Forbidden", response=response)
            
            # Raise an exception for other bad responses
            response.raise_for_status()
            
            # Parse the response data
            parsed_data = parse_data(response.json())
            data.extend(parsed_data)
            
            # Check for more pages
            link_header = response.headers.get('Link')
            pages_remaining = link_header and 'rel="next"' in link_header
            
            if pages_remaining:
                # Extract next page URL
                url = next_pattern.search(link_header).group(1)
            
            # Reset retries on successful request
            retries = 0
        
        except requests.exceptions.RequestException as e:
            print(f"Request error occurred: {e}")
            retries += 1
            
            if retries >= max_retries:
                print(f"Max retries ({max_retries}) reached. Stopping.")
                break
            
            # Exponential backoff
            wait_time = 2 ** retries
            print(f"Retrying in {wait_time} seconds... (Attempt {retries})")
            time.sleep(wait_time)
    
    return data

def save_to_json(data, filename=None):
    """
    Save data to a JSON file. If no filename is provided, 
    generate a filename based on current timestamp.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"github_data_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Data saved to {filename}")
    return filename

def save_to_csv(data, filename=None):
    """
    Save data to a CSV file. If no filename is provided, 
    generate a filename based on current timestamp.
    """
    if not data:
        print("No data to save.")
        return None

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"github_data_{timestamp}.csv"
    
    # Determine which keys to use based on the first item
    first_item = data[0]
    keys = []
    
    def flatten_dict(d, parent_key='', sep='_'):
        """Flatten nested dictionaries"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string to avoid CSV issues
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    # Flatten the first item to get keys
    flattened_first_item = flatten_dict(first_item)
    keys = list(flattened_first_item.keys())
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        
        for item in data:
            writer.writerow(flatten_dict(item))
    
    print(f"Data saved to {filename}")
    return filename

def main():
    # URL for api call
    url = "https://api.github.com/enterprises/my-enterprise/audit-log?phrase=created%3A%3E%3D2025-03-18T00%3A00%3A00+00%3A00+action%3Agit.clone&include=git"
    
    try:
        # Retrieve data
        audit_log = get_paginated_data(url)
        
        print(f"Total entries retrieved: {len(audit_log)}")
        
        # Save to JSON
        json_filename = save_to_json(audit_log)
        
        # Save to CSV
        csv_filename = save_to_csv(audit_log)
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
