# Deep-Research-Agent
Deep Research workflow relying on AI agents, developed with LangGraph.
This project explores how agentic workflows can go beyond a single LLM call by iteratively generating search queries, gathering sources, and reflecting on knowledge gaps until a satisfactory answer is produced. It is an exploratory / learning project and is not intended for production use.


### What the agent does

- Generates multiple search queries from a user question
- Executes web searches in parallel
- Aggregates and grounds information with citations
- Reflects on potential knowledge gaps
- Iterates until the answer is deemed sufficient or a loop limit is reached.

The graph structure of the worflow can be found in the `./outputs` folder. The final answer is returned as a Markdown-formatted text in the same folder.


### How to run the code

It can only be run from the command line. The format has to be the following:
```bash
python ./deep_research_agent.py "What are the latest developments in quantum mechanics" --max-loops=2 --initial-queries=3
```


### Future improvements

I might improve on this code in the future by:
- Adding a frontend to visualize the conversation flow and the agent’s reasoning steps.
- Tracking token usage and exposing more configuration options.
- Providing a Dockerfile for easier execution across. 


### License 

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.


### Reference 

This project is inspired by the following Google repository: https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart