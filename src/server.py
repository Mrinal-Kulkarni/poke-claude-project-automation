#!/usr/bin/env python3
import os
import anthropic
from github import Github
from fastmcp import FastMCP
import requests

mcp = FastMCP("Project Development Server")

@mcp.tool(description="Develop an idea using Claude and create a GitHub repo with project spec")
def develop_and_create_project(
    idea: str,
    project_name: str
) -> dict:
    """
    Takes an idea, develops it with Claude, and creates a GitHub repo with project spec.
    
    Args:
        idea: The initial project idea to develop
        project_name: Name for the GitHub repository
    
    Returns:
        Dictionary with GitHub repo URL and developed spec
    """
    
    # 1. Use Claude API to develop the idea
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""You are a product development expert. Take this idea and develop it into a detailed project specification:

Idea: {idea}

Please provide:
1. Project Overview (2-3 sentences)
2. Key Features (bullet points)
3. Technical Architecture (brief description)
4. Implementation Phases (3-5 phases)
5. Success Metrics

Format this as a well-structured markdown document suitable for a README.md"""
        }]
    )
    
    developed_spec = response.content[0].text
    
    # 2. Create GitHub repository
    g = Github(os.environ.get("GITHUB_TOKEN"))
    user = g.get_user()
    
    repo = user.create_repo(
        name=project_name,
        description=f"Project: {idea[:100]}",
        private=False,
        auto_init=True
    )
    
    # 3. Create README.md with the spec
    repo.create_file(
        path="README.md",
        message="Initial project specification",
        content=developed_spec
    )
    
    result = {
        "github_url": repo.html_url,
        "spec": developed_spec,
        "status": "success"
    }
    
    return result

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting FastMCP server on {host}:{port}")
    
    mcp.run(
        transport="http",
        host=host,
        port=port
    )
