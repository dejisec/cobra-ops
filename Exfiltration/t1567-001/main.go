package main

import (
	"context"
	"encoding/base64"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/google/go-github/v68/github"
	"golang.org/x/oauth2"
)

const (
	// Replace with your GitHub personal access token
	githubToken = "your-github-token-here"

	// Repository settings
	repoOwner = "your-username"
	repoName  = "your-repo-name"
	branch    = "main"
)

var branchName = branch

func main() {
	message := flag.String("message", "Upload file", "Commit message")
	file := flag.String("file", "", "Local file to upload")
	flag.Parse()

	if *file == "" {
		fmt.Println("Error: File path is required")
		flag.PrintDefaults()
		os.Exit(1)
	}

	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: githubToken},
	)
	tc := oauth2.NewClient(ctx, ts)
	client := github.NewClient(tc)

	content, err := os.ReadFile(*file)
	if err != nil {
		fmt.Printf("Error reading file: %v\n", err)
		os.Exit(1)
	}

	repoPath := filepath.Base(*file)

	encodedContent := base64.StdEncoding.EncodeToString(content)

	var sha *string
	currentFile, _, _, err := client.Repositories.GetContents(ctx, repoOwner, repoName, repoPath, &github.RepositoryContentGetOptions{
		Ref: branch,
	})
	if err == nil && currentFile != nil {
		sha = currentFile.SHA
	}

	opts := &github.RepositoryContentFileOptions{
		Message: message,
		Branch:  &branchName,
		Content: []byte(encodedContent),
		SHA:     sha,
	}

	_, _, err = client.Repositories.CreateFile(ctx, repoOwner, repoName, repoPath, opts)
	if err != nil {
		fmt.Printf("Error uploading file: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Successfully uploaded %s to %s/%s\n", *file, repoName, repoPath)
}
