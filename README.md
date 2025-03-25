# gh-api-paginated
Fetches GitHub Logs and outputs them to CSV/JSON.  
Useful for big queries where pagination is needed.

## How to use
- Create a PAT with the permissions required for your operation.  
Export it as GITHUB_TOKEN or input it on each run.  
- Set the url variable in main function.
Example: ```"https://api.github.com/enterprises/my-enterprise/audit-log?phrase=created%3A%3E%3D2025-03-18T00%3A00%3A00+00%3A00+action%3Agit.clone&include=git"```
- Run it.

