import os
from typing import Optional

import requests
import toml
import typing_extensions as t
from dotenv import load_dotenv
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, ConfigDict, GetJsonSchemaHandler, create_model
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema as cs

load_dotenv()
pyproject = toml.load("pyproject.toml")
version = pyproject["project"]["version"]

TYPEMAP = {
    "integer": int,
    "number": float,
    "array": list,
    "boolean": bool,
    "string": str,
    "null": type(None),
}

FIELD_DEFAULTS = {
    int: 0,
    float: 0.0,
    list: [],
    bool: False,
    str: "",
    type(None): None,
}


def configure_field(
    name: str, type_: dict[str, t.Any], required: list[str]
) -> tuple[type, t.Any]:
    field_type = TYPEMAP[type_["type"]]
    default_ = FIELD_DEFAULTS.get(field_type) if name not in required else ...
    return field_type, default_


def create_schema_model(schema: dict[str, t.Any]) -> type[BaseModel]:
    # Create a new model class that returns our JSON schema.
    # LangChain requires a BaseModel class.
    class SchemaBase(BaseModel):
        model_config = ConfigDict(extra="allow")

        @t.override
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return schema

    # Since this langchain patch, we need to synthesize pydantic fields from the schema
    # https://github.com/langchain-ai/langchain/commit/033ac417609297369eb0525794d8b48a425b8b33
    required = schema.get("required", [])
    fields: dict[str, t.Any] = {
        name: configure_field(name, type_, required)
        for name, type_ in schema["properties"].items()
    }

    return create_model("Schema", __base__=SchemaBase, **fields)


class MkinfTool(BaseTool):
    api_key: Optional[str] = None
    repo_owner: str
    repo_name: str
    repo_action: str
    repo_version: Optional[str] = None
    args_schema: Optional[type[BaseModel]] = None
    env: Optional[dict[str, Optional[str]]]
    timeout: Optional[int] = 60
    session_id: Optional[str] = None

    # def __init__(
    #     self,
    #     repo_owner: str,
    #     repo_name: str,
    #     repo_action: str,
    #     env: Optional[dict[str, Optional[str]]],
    #     initialize: bool = False,
    #     api_key: Optional[str] = None,
    #     repo_version: Optional[str] = None,
    #     args_schema: Optional[type[BaseModel]] = None,
    #     timeout: Optional[int] = 60,
    #     session_id: Optional[str] = None,
    #     **kwargs,
    # ):
    #     super().__init__(
    #         repo_owner=repo_owner,
    #         repo_name=repo_name,
    #         repo_action=repo_action,
    #         env=env,
    #         timeout=timeout,
    #         session_id=session_id,
    #         api_key=api_key or os.getenv("MKINF_API_KEY"),
    #         **kwargs,
    #     )

    #     if initialize:
    #         self.start_session()

    @t.override
    def _run(self, **kwargs: t.Any) -> t.Any:
        from requests import post

        try:
            if self.session_id is None:
                response = post(
                    url=f"http://localhost:3434/v1/{self.repo_owner}/{self.repo_name}/{self.repo_action}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "args": kwargs,
                        "env": self.env,
                        "timeout": self.timeout,
                        "client_version": version,
                    },
                )
            else:
                response = post(
                    url=f"http://localhost:3434/v1/sessions/{self.session_id}/{self.repo_action}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "args": kwargs,
                        "timeout": self.timeout,
                        "client_version": version,
                    },
                )
            return response.json()
        except Exception as e:
            print(f"ERROR: {e}")
            raise ToolException(e)

    @property
    def tool_call_schema(self) -> type[BaseModel]:
        assert self.args_schema is not None  # noqa: S101
        return self.args_schema

    def start_session(self):
        from requests import post

        try:
            print(f"http://localhost:3434/v1/{self.repo_owner}/{self.repo_name}/")
            response = post(
                url=f"http://localhost:3434/v1/{self.repo_owner}/{self.repo_name}/",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "env": self.env,
                    "timeout": self.timeout,
                    "client_version": version,
                },
            )
            if not response.ok:
                raise ToolException(f"Failed to initialize session: {response.text}")
            print("RESPONSE")
            self.session_id = response.json()["data"]["session_id"]
            print("SESSION ID:", self.session_id)
            return response.json()
        except Exception as e:
            print(f"ERROR: {e}")
            raise ToolException(e)

    def close_session(self):
        pass
        # from requests import delete

        # try:
        #     response = delete(
        #         url=f"http://localhost:3434/v1/{self.repo_owner}/{self.repo_name}/",
        #         headers={"Authorization": f"Bearer {self.api_key}"},
        #         json={"session_id": self.session_id},
        #     )
        #     self.session_id = None
        #     return response.json()
        # except Exception as e:
        #     print(f"ERROR deleting session: {e}")

    def __del__(self):
        pass
        # if self.session_id:
        #     from requests import delete

        #     try:
        #         delete(
        #             url=f"http://localhost:3434/v1/{self.repo_owner}/{self.repo_name}/",
        #             headers={"Authorization": f"Bearer {self.api_key}"},
        #             json={"session_id": self.session_id},
        #         )
        #     except Exception as e:
        #         print(f"ERROR deleting session: {e}")


def pull(
    repos: list[str],
    env: Optional[dict[str, Optional[str]]] = None,
    timeout: Optional[int] = 60,
    initialize: bool = False,
    api_key: Optional[str] = None,
) -> list[BaseTool]:
    if not api_key and not os.getenv("MKINF_API_KEY"):
        raise ValueError("Missing MKINF_API_KEY")
    tools = []
    res = requests.get(
        url="https://api.mkinf.io/v0.2/releases",
        params={"ids": repos},
        headers={"Authorization": f"Bearer {api_key or os.getenv('MKINF_API_KEY')}"},
    )
    if res.status_code != 200:
        raise Exception("Can't load tools")
    for repo in res.json()["data"]:
        # TODO: Get correct version
        release = repo.get("releases", [])[0]
        for action in release["actions"]:
            tool = MkinfTool(
                name=f"{repo['owner']}__{repo['name']}__{action['action']}",
                description=action["description"],
                repo_owner=repo["owner"],
                repo_name=repo["name"],
                repo_action=action["action"],
                args_schema=create_schema_model(action.get("input_schema", None)),
                env=env,
                timeout=timeout,
                api_key=api_key or os.getenv("MKINF_API_KEY"),
            )
            if initialize:
                tool.start_session()
            tools.append(tool)
    return tools
