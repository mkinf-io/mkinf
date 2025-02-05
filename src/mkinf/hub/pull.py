import os
import requests
import json
import toml
from langchain_core.tools import BaseTool
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
pyproject = toml.load("pyproject.toml")
version = pyproject["project"]["version"]
print("mkinf SDK version", version)

def pull(repos: list[str], env: Optional[dict[str, str]] = None) -> list[BaseTool]:
    if not os.getenv('MKINF_API_KEY'):
        raise ValueError("Missing MKINF_API_KEY")

    tools = []
    res = requests.get(
        url="https://api.mkinf.io/v0.2/releases",
        params={"ids": repos},
        headers={"Authorization": f"Bearer {os.getenv('MKINF_API_KEY')}"}
    )
    if res.status_code != 200:
        raise Exception("Can't load tools")
    for repo in res.json()["data"]:
        # TODO: Get correct version
        release = repo.get("releases", [])[0]
        for action in release["actions"]:
            params = ", ".join(action["input_schema"].keys())
            method_body = f"""
def _run(self, {params}):
    import requests
    try:
        # Build the body dynamically from parameters
        args = {{{", ".join(f'"{param}": {param}' for param in action["input_schema"].keys())}}}
        response = requests.post(
            url="https://run.dev.mkinf.io/v0.1/{repo["owner"]}/{repo["name"]}/{action["action"]}",
            headers={{"Authorization": "Bearer {os.getenv('MKINF_API_KEY')}"}},
            json={{ "args": args, "env": {json.dumps(env) if env else None}, "client_version": "{version}" }}
        )
        return response.json()
    except Exception as e:
        print(f"ERROR: {{e}}")
        return {{"error": str(e)}}
"""
            class_attributes = {}
            exec(method_body, {}, class_attributes)
            DynamicClass = type(
                f"{repo['owner']}__{repo['name']}__{action['action']}",
                (BaseTool,),
                {
                    "__annotations__": {
                        "name": str,
                        "description": str,
                    },
                    "name": Field(default=f"{repo['owner']}__{repo['name']}__{action['action']}"),
                    "description": Field(default=action["description"]),
                    "_run": class_attributes["_run"],
                },
            )
            tools.append(DynamicClass())

    return tools
