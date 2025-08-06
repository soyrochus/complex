Target-file: tristore/cypher_llm_repl.py

The current implementation is a REPL for Cypher queireis to a Postgres database

The new implementatin in the aforementioned file should be a variation but where all communication passes trhough an LLM

Do no change the execution of cypherfiles via the command line 

when opened as repl any prompt should be send to an LLM via Langchain. Use v0.3 libs/syntax etc. 

the LLM can decide to invoke a tool "send_cypher" to get/set data from the database

AFter tool invocation the data is send to the LLM for possible postprocessing and then the data is retunred to the REPL

This allows natural language queiries of a Postrgress database with the age graph extensions

Create the tool and implement the Lanchain invocation in such a way that tool invocation is supported 

For the moment use OpenAI gpt4.1 as model (using langchanin). OpenAI parameters set in example.env (i will create the .env file) and retrived from os environment. 

TRhere should be an optional parameter which would allow to point to a txt or md file with a system prompt