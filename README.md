# mkinf SDK
![PyPI - Version](https://img.shields.io/pypi/v/mkinf)

The mkinf SDK is a powerful toolkit that allows you to easily integrate MCP servers into your applications. With mkinf, you can access a growing ecosystem of specialized AI capabilities through a simple, unified interface.

## Getting Started
Follow these steps to start using mkinf in your projects:

## 1. Create a mkinf Account
Sign up for a free account at [hub.mkinf.io/signup](https://hub.mkinf.io/signup).
<Check>During the beta period, all accounts receive unlimited free credits</Check>

## 2. Configure Your API Key
1. Go to [API Keys settings](https://hub.mkinf.io/settings/api-keys)
2. Create an organization if you haven't already
3. Generate and copy your API key
4. Add the key to your project's `.env` file:

```env .env
MKINF_API_KEY=sk-org-...
```

## 3. Install the SDK
Install the mkinf SDK using pip:

```bash
pip install mkinf
```

For specific versions, check the [PyPI repository](https://pypi.org/project/mkinf/).

## 4. Find an AI Agent
Browse available AI Agents at [mkinf hub](https://hub.mkinf.io/) and select an agent that matches your use case

![image](https://github.com/user-attachments/assets/0ff5509f-e376-41d6-9727-29eea5221062)

## 5. Import and Use the Agent
Check the "Use Agent" section of your chosen repository for import instructions

![image](https://github.com/user-attachments/assets/74e69f77-c452-4e82-82ef-824e9c48a20a)

Import the agent into your code

```python
from mkinf import hub as mh

tools = mh.pull(
    ["ScrapeGraphAI/scrapegraphai"],
    env={
        "SCRAPEGRAPH_LLM_MODEL": "openai/gpt-4o-mini",
        "SCRAPEGRAPH_LLM_API_KEY": os.getenv("OPENAI_API_KEY")
    }
)
```

> [!NOTE]
> Remember to configure any required environment variables specified in the agent's documentation.

## Current Limitations

> [!WARNING]
> Currently, mkinf tools are compatible with LangChain chains and graphs. Support for other frameworks like CrewAI, AutoGen, and SmolAgents is coming soon.

# Example
You can run the included Streamlit example to see mkinf in action:
```bash
uv run sync --dev
uv run example
```