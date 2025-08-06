Target-file: tristore/cypher_llm_repl.py

Implement in the repl two commands:

\log [on|off] (or true|false)  - this will show the output of the LLM and database connections (clearly marked as such to see what is the differnce) . Default OFF

\llm [on|off] (or true|false)  - When OFF, the repl input is directly passed to the database, assuming that the input is a Cypher query or expression. Default ON


