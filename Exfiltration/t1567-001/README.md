# T1567.001 - Exfiltration Over Web Service: Exfiltration to Code Repository

Implementation of [T1567.001](https://attack.mitre.org/techniques/T1567/001) - Exfiltration Over Web Service: Exfiltration to Code Repository.

## Features

- Upload files to a GitHub repository

## Prerequisites

- [Go](https://golang.org)
- [Task](https://taskfile.dev) for building (optional)
- GitHub Personal Access Token with `Read` and `Write` access to `Contents` of a repository

## Setup

1. Configure your GitHub credentials:

   - Replace the following constants in `main.go` with your values:

     ```go
     githubToken = "your-github-token-here"
     repoOwner   = "your-username"
     repoName    = "your-repo-name"
     ```

2. Install dependencies:

    ```bash
    # Using task
    task install-deps

    # Or using go directly
    go mod tidy
    ```

## Build

You can build the application using Task or Go directly.

### Using Task

Build for your current platform:

```bash
task build
```

Build for specific platforms:

```bash
task build-linux   # Build Linux binaries (amd64, arm64)
task build-darwin  # Build macOS binaries (amd64, arm64)
task build-windows # Build Windows binaries (amd64, 386)
```

### Using Go Directly

Build for your current platform:

```bash
go build -o build/t1567-001 main.go
```

## Usage

The application accepts two command-line flags:

- `-file`: Path to the file you want to upload (required)
- `-message`: Commit message (optional, defaults to "Upload file")

Example:

```bash
# Using the built binary
./build/t1567.001 -file path/to/file.txt -message "T1567.001"

# Using go directly
go run main.go -file path/to/file.txt -message "T1567.001"
```

The file will be uploaded to the root of your configured GitHub repository using the same filename.
