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
    project_name: str,
    create_notion_page: bool = True
) -> dict:
    """
    Takes an idea, develops it with Claude, creates a GitHub repo, and optionally creates a Notion page.
    
    Args:
        idea: The initial project idea to develop
        project_name: Name for the GitHub repository
        create_notion_page: Whether to create a Notion page for project management
    
    Returns:
        Dictionary with GitHub repo URL, developed spec, and Notion page URL if created
    """
    
    # 1. Use Claude API to develop the idea
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""You are a product development expert. Take this idea and develop it into a comprehensive project specification.

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
    
    # 4. Optionally create Notion page
    if create_notion_page and os.environ.get("NOTION_API_KEY"):
        notion_page = create_notion_project_page(idea, project_name, repo.html_url)
        result["notion_url"] = notion_page
    
    return result

@mcp.tool(description="Create a Notion page for project management")
def create_notion_project_page(idea: str, project_name: str, github_url: str) -> str:
    """Create a Notion page for project management"""
    
    notion_api_key = os.environ.get("NOTION_API_KEY")
    notion_database_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not notion_api_key or not notion_database_id:
        return "Notion integration not configured"
    
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": notion_database_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": project_name}}]
            },
            "Status": {
                "status": {"name": "In Progress"}
            },
            "GitHub": {
                "url": github_url
            }
        },
        "children": [{
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Project Idea"}}]
            }
        }, {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": idea}}]
            }
        }]
    }
    
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json().get("url", "Page created but URL not available")
    else:
        return f"Error creating Notion page: {response.status_code}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting FastMCP server on {host}:{port}")
    
    mcp.run(
        transport="http",
        host=host,
        port=port
    )
