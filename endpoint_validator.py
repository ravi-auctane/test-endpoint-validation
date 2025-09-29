#!/usr/bin/env python3
"""
Endpoint validator for GitHub Actions
Validates that new API endpoints follow allowed parent paths
"""
import os
import sys
import json
import re
import argparse
from pathlib import Path

# Configuration - Modify these paths to match your project's API structure
ALLOWED_PARENT_PATHS = [
    "/api/v1",
    "/api/v2",
    "/api/v3",
    # Add your allowed parent paths here
]

# File extensions to check
FILE_EXTENSIONS = ['.go', '.js', '.ts', '.py', '.java', '.rb']

# Endpoint patterns for different languages/frameworks
ENDPOINT_PATTERNS = {
    'go': [
        # Gorilla Mux
        r'\.HandleFunc\s*\(\s*["`]([^"`]+)["`]',
        # Gin
        r'\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["`]([^"`]+)["`]',
        # Echo
        r'e\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["`]([^"`]+)["`]',
        # Standard http
        r'http\.HandleFunc\s*\(\s*["`]([^"`]+)["`]',
    ],
    'js': [
        # Express/Node.js
        r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        # Fastify
        r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
    ],
    'ts': [
        # TypeScript (similar to JS)
        r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        # NestJS
        r'@(Get|Post|Put|Delete|Patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
    ],
    'py': [
        # Flask
        r'@app\.route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        # FastAPI
        r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        # Django
        r'path\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
    ],
    'java': [
        # Spring Boot
        r'@(?:Get|Post|Put|Delete|Patch)Mapping\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        r'@RequestMapping\s*\(.*path\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
    ],
    'rb': [
        # Rails/Ruby
        r'(?:get|post|put|delete|patch)\s+[\'"`]([^\'"`]+)[\'"`]',
    ],
}

def get_changed_files():
    """Get list of changed files from git"""
    try:
        # Check if we're in a GitHub Actions PR context
        if os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
            # For PRs, get the base branch
            base = os.environ.get('GITHUB_BASE_REF', 'main')
            # Fetch the base branch to ensure we have it
            os.system(f"git fetch origin {base} --depth=1 2>/dev/null")
            cmd = f"git diff --name-only origin/{base}...HEAD"
        else:
            # For push events, compare with previous commit
            cmd = "git diff --name-only HEAD~1"
        
        result = os.popen(cmd).read().strip()
        if not result:
            return []
        
        files = result.split('\n')
        # Filter for relevant file extensions and existing files
        return [
            f for f in files 
            if f and os.path.exists(f) and 
            any(f.endswith(ext) for ext in FILE_EXTENSIONS)
        ]
    except Exception as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        return []

def extract_endpoints_from_file(filepath):
    """Extract API endpoints from a source file"""
    endpoints = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine file type
        file_ext = Path(filepath).suffix[1:]  # Remove the dot
        patterns = ENDPOINT_PATTERNS.get(file_ext, [])
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                # Extract the endpoint path
                if isinstance(match, tuple):
                    # Some patterns capture method and path
                    endpoint = match[1] if len(match) > 1 and match[1].startswith('/') else match[0]
                else:
                    endpoint = match
                
                # Only add valid endpoints (starting with /)
                if endpoint and endpoint.startswith('/'):
                    # Clean up the endpoint (remove query params, etc.)
                    endpoint = endpoint.split('?')[0].split('#')[0]
                    endpoints.append(endpoint)
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    
    return endpoints

def validate_endpoint(endpoint):
    """Check if an endpoint follows allowed parent paths"""
    # Remove trailing slashes for comparison
    endpoint = endpoint.rstrip('/')
    
    for parent_path in ALLOWED_PARENT_PATHS:
        parent_path = parent_path.rstrip('/')
        if endpoint.startswith(parent_path + '/') or endpoint == parent_path:
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Validate API endpoints against allowed parent paths')
    parser.add_argument('--changed-only', action='store_true',
                       help='Only check files changed in the last commit/PR')
    parser.add_argument('--output-json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--all-files', action='store_true',
                       help='Check all files in the repository')
    
    args = parser.parse_args()
    
    # Get files to check
    if args.changed_only:
        files_to_check = get_changed_files()
        if not files_to_check:
            print("No changed files to check" if not args.output_json else 
                  json.dumps({"success": True, "message": "No changed files to check"}))
            sys.exit(0)
    elif args.all_files:
        files_to_check = []
        for ext in FILE_EXTENSIONS:
            files_to_check.extend(Path('.').rglob(f'*{ext}'))
        files_to_check = [str(f) for f in files_to_check]
    else:
        # Default to changed files
        files_to_check = get_changed_files()
    
    # Extract and validate endpoints
    all_endpoints = []
    violations = []
    
    for filepath in files_to_check:
        endpoints = extract_endpoints_from_file(filepath)
        for endpoint in endpoints:
            endpoint_info = {
                'file': filepath,
                'endpoint': endpoint
            }
            all_endpoints.append(endpoint_info)
            
            if not validate_endpoint(endpoint):
                violations.append(endpoint_info)
    
    # Output results
    if args.output_json:
        result = {
            'success': len(violations) == 0,
            'files_checked': len(files_to_check),
            'total_endpoints': len(all_endpoints),
            'violations': violations,
            'allowed_paths': ALLOWED_PARENT_PATHS
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"🔍 Endpoint Validation Report")
        print(f"{'='*50}")
        print(f"Files checked: {len(files_to_check)}")
        print(f"Endpoints found: {len(all_endpoints)}")
        print(f"Violations: {len(violations)}")
        
        if violations:
            print(f"\n❌ Invalid endpoints detected:\n")
            for v in violations:
                print(f"  File: {v['file']}")
                print(f"  Endpoint: {v['endpoint']}")
                print()
            
            print(f"Allowed parent paths:")
            for path in ALLOWED_PARENT_PATHS:
                print(f"  ✓ {path}")
        else:
            print(f"\n✅ All endpoints are valid!")
    
    # Exit with appropriate code
    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()