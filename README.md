# gh-api-paginated
Fetches GitHub Logs and outputs them to CSV/JSON.  
Useful for big queries where pagination is needed.

## How to use
- Create a PAT with the permissions required for your operation.  
Export it as GITHUB_TOKEN or input it on each run.  
- Run it: 
```
python github-api-paginated.py --from-date 2025-03-25 --enterprise my-enterprise --action git.clone --include git
```

