# Agentic AI using Langgraph with Azure OpenAI and 3rd party tools

## Description

This repo contains scripts for running chatbots leveraging Open AI and other llms. It provides an example of what can be done using langgraph with different LLMs like Azure OpenAI

## Prereqs

- Azure OpenAI instance  [Deploying Azure OpenAI Instance](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal)
- [Tavily](https://tavily.com/) API Key.
- Python 3.11.x

## Running the demos

### Azure Open AI

The demos are located in the src/dev/ directory

Set the environment variables

```sh
export OPENAI_API_KEY="<API Key>"
export TAVILY_API_KEY="<API Key>"
```

```sh
python testopenai.py
```

### General LLM demo

```sh
export 
export TAVILY_API_KEY="<API Key>"
```

