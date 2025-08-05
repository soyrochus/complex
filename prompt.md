Create a prompt instrcuting a coding agent like OpenAI's Codex or Anthropic CLaude to generate the library Complex (module name  "complex" ) as sepcified in the doc below. 

Implementation in Python to create a 
parser (complex.parser)
interpreter (complex.interpreter)
and all corresponding mechanism to execute PostgreSQL and Cypher quieries according to the Grammar and ALL funcionality specified below
THe library should use psycopg2 to interact with the database. Assume a working postrgressl with Age extension

the module should return sensible status and error messages mapped to the SDL from the underlying run-time

The module should work "life", i.e. directly with the underlying database. No precompilation should be needed

all parameters needed (database url, name, password, graph db nme etc) should be set by environmnet variable which the user should be able to set with .env (python-dotenv)

you should use pytest to implement use cases (where possible using the examples from the doc)

THere should be a minmal cli (complex.cli) to allow for direct inteterction with the database.

The documentation:

Formal Specification of Complex (extended type system)
0. Extended Grammar (EBNF /Lark‑style)
(* 0. Lexical tokens *)

<TypeName>      ::= CNAME                     (* user‑defined entity *)

<FieldName>     ::= CNAME

<RelName>       ::= CNAME

<PrimitiveType> ::= "STRING" | "INT" | "FLOAT" | "BOOL"

                 | "DATE" | "DATETIME" | "BLOB" | "UUID" | "JSON"

<Literal>       ::= STRING | SIGNED_NUMBER | "TRUE" | "FALSE" | "NULL"

(* 1. Schema definition *)

<entity_def>      ::= "ENTITY" <TypeName> "{" <field_list> "}" [ "EXTENDS" <BaseType> ] ";"

<field_list>      ::= <field_decl> ( "," <field_decl> )*

<field_decl>      ::= <FieldName> ":" <DataType>

<DataType>        ::= <PrimitiveType>

                    | <TypeName>                   (* reference to another entity *)

                    | <TypeName> "[]"             (* multi‑valued reference *)

<relationship_def>::= "RELATIONSHIP" <RelName>

                      "(" <SourceType> [ <Mult> ] "->" <TargetType> [ <Mult> ] ")"

                      [ "{" <field_list> "}" ] ";"

<Mult>            ::= "1" | "*"                    (* one / many *)

(* 2. Data insertion *)

<insert_entity>   ::= "INSERT" <TypeName> "{" <assign_list> "}" [ "AS" <alias> ] ";"

<assign_list>     ::= <assign> ( "," <assign> )*

<assign>          ::= <FieldName> "=" <Literal_or_ref>

<Literal_or_ref>  ::= <Literal> | <alias_or_id>

<connect_rel>     ::= "CONNECT" <alias_or_id> "-" <RelName> "->" <alias_or_id>

                      [ "{" <assign_list> "}" ] ";"

(* 3. Updates / Deletes *)

<update_stmt>     ::= "UPDATE" <target_ref> "SET" <assign_list> ";"

<delete_stmt>     ::= "DELETE" <target_ref> ";"

<target_ref>      ::= <alias_or_id>

                    | <TypeName> "{" <condition> "}"

<condition>       ::= <prop_eq> { ( "AND" | "OR" ) <prop_eq> }

(* 4. Query *)

<query_stmt>      ::= "MATCH" <pattern> [ "WHERE" <condition> ] [ "RETURN" <return_list> ] ";"

(* node / edge patterns identical to previous version *)

(* 5. Auxiliary *)

<alias_or_id>     ::= <alias> | SIGNED_NUMBER
Notes:
<DataType> accepts a <TypeName> – this allows entity references in a field list.
Array notation (TypeName[]) expresses multi‑valued references (one‑to‑many) without needing a separate relationship definition.
<Literal_or_ref> lets a field be set either to a primitive literal or to the alias/ID of an existing entity instance (reference assignment).
DELETE is added for completeness (nodes or edges can be deleted after being matched).

Manual; hands-on guide to Complex
1  Define entity types (now with reference fields)
ENTITY Employee {

    name: STRING,

    manager: Employee,            -- single (recursive) reference

    reports: Employee[],          -- multi‑valued reference (tree/DAG)

    hire_date: DATE,

    badge_id: UUID

};

ENTITY Document {

    title: STRING,

    sections: STRING[]            -- simple string list

};

ENTITY Epic {

    name: STRING,

    parent: Epic[],               -- epics can nest arbitrarily

    specification: Document       -- direct link to a Document entity

};

Employee.manager is a single reference to another Employee.
Employee.reports is a collection of Employee references ([]).
Primitive fields remain unchanged.


2  Define relationship types
Relationships are still the preferred way to model semantically rich links or those that carry edge properties.

RELATIONSHIP IN_DOCUMENT (Epic 1 -> Document *) { page_number: INT };

RELATIONSHIP COLLABORATES_WITH (Employee * -> Employee *) ;


3  Create entity instances
INSERT Employee { name="Alice" }                AS alice;

INSERT Employee { name="Bob", manager=alice }   AS bob;

INSERT Employee { name="Carol", manager=alice, reports=[bob] } AS carol;

INSERT Document { title="Order Processing" }    AS docOrder;

INSERT Epic { name="Processing orders", specification=docOrder } AS epicProc;

Reference assignment uses aliases created in the same script (manager=alice).
Multi‑valued fields use [ … ] bracket syntax.


4  Populate reference fields later
UPDATE bob SET reports=[carol];

Or swap a reference:

UPDATE epicProc SET specification = docOrderV2;


5  Create relationships (when edge properties are needed)
CONNECT epicProc - IN_DOCUMENT -> doccypher Order { page_number = 42 };


6  Query (including edge properties & reference navigation)
MATCH (e:Employee {name="Alice"})-[:COLLABORATES_WITH]->(peer:Employee)

RETURN peer.name;

MATCH (epic:Epic)-[inDoc:IN_DOCUMENT]->(doc:Document)

RETURN epic.name, inDoc.page_number, doc.title;

Reference‑fields can be followed via property access in the interpreter (implementation‑specific) or by explicit relationships if mapped to edges at runtime.



From the grammar as defined before we can build six orthogonal “options” when writing a query:

#
What you may vary
Options allowed by the grammar
Notes
1
Node specification
• With alias & label (n:Person)  
• Label only `(:Person)`
• Alias only (*illegal* – label is mandatory)

• Add inline property filters `(n:Person {name="Alice"})`
Property filters = comma‑separated equality tests
2
Edge specification
• Bare anonymous edge -[]- 
• Named type `-[ :FRIEND ]-`
• Alias plus type `-[r:FRIEND]-` (if you extend grammar with alias capture)

• Edge property filters `-[ :IN_DOCUMENT {page_number=42} ]-`
Both relationship name and properties are optional.
3
Direction
--> (outgoing), <-- (incoming), -- (undirected)
Achieved by putting the arrow head on one side of the edge pattern.
4
Path length
One or many hops: the (node)-(edge)-(node) sequence can repeat any number of times.
No variable‑length (*..*) quantifiers in the base grammar.
5
Additional boolean filtering (WHERE)
Chain of property = literal conditions combined with AND / OR.
No <, >, functions, or parentheses in v1 grammar.
6
Return clause
• Entire subgraph omitted (no RETURN) 
• One or more node aliases `RETURN n, m`

• Property projections `RETURN n.name, r.page_number`
return_item is either an alias or alias.field.



Examples that cover each option
Single node, property filter, implicit return of full match

MATCH (e:Employee {name="Alice"});

Typed edge with direction and alias, projecting edge property

MATCH (epic:Epic)-[inDoc:IN_DOCUMENT]->(d:Document)

RETURN epic.name, inDoc.page_number, d.title;

Edge without a type (wild‑card), explicit WHERE filter

MATCH (a:Person)-[r]->(b:Person)

WHERE r.since = 2020 AND a.name = "Alice"

RETURN b.name;

Multi‑hop pattern

MATCH (a:Employee)-[:REPORTS_TO]-(:Employee)-[:REPORTS_TO]->(boss:Employee)

RETURN boss.name;
Where reference fields fit in
Reference navigation can be realised in two implementation strategies:

Strategy
How you query
Interpreter responsibility
Edge‑mapped references (preferred for graph DBs)
Use an explicit edge pattern, as shown above ((:Epic)-[:SPECIFICATION]->(:Document))
Interpreter turns reference‑typed fields declared in the schema into real AGE edges at insert time.
Property projection (references stored as IDs)
Treat the field as a scalar and resolve it in application code: MATCH (e:Epic) RETURN e.specification
Interpreter must map specification to a document ID and optionally do a second lookup.


The grammar itself is agnostic: it allows either pattern because it just sees property names and edge patterns.

Limitations of the current grammar
No inequality operators, functions, regex, or ranges in WHERE.
No aggregations (COUNT, MAX, …).
No variable‑length edge patterns (*, 1..3, etc.).
No ordering (ORDER BY) or pagination (LIMIT).

All of these could be added in a future revision while keeping backward compatibility.

7  Change / delete
UPDATE alice SET badge_id = "a1b2c3d4-e" ;

MATCH (e:Employee {name="Bob"}) DELETE e;             -- delete node

MATCH (epic:Epic)-[r:IN_DOCUMENT]->(d:Document) DELETE r;  -- delete edge


8  Evolve the schema
Add a new primitive field or reference:

ENTITY Employee {

    name: STRING,

    manager: Employee,

    reports: Employee[],

    hire_date: DATE,

    badge_id: UUID,

    location: STRING           -- new field

};

Add an optional relationship property:

RELATIONSHIP COLLABORATES_WITH (Employee * -> Employee *) { since: DATE };


9  Full script template
-- 1. Schema -------------------------------------------------

ENTITY Employee { name: STRING, manager: Employee, reports: Employee[] };

ENTITY Document { title: STRING };

ENTITY Epic     { name: STRING, specification: Document };

RELATIONSHIP IN_DOCUMENT (Epic 1 -> Document *) { page_number: INT };

-- 2. Data ---------------------------------------------------

INSERT Employee { name="Alice" }                      AS alice;

INSERT Employee { name="Bob",   manager=alice }       AS bob;

INSERT Document { title="Order Processing" }          AS docOrder;

INSERT Epic     { name="Processing orders", specification=docOrder } AS epicProc;

CONNECT epicProc - IN_DOCUMENT -> docOrder { page_number = 42 };

-- 3. Query --------------------------------------------------

MATCH (epic:Epic)-[inDoc:IN_DOCUMENT]->(doc:Document)

RETURN epic.name, inDoc.page_number;

Run via:

dataspec run example.dsl

Take‑aways with the extended type system
Category
What you use
Notes
Primitive data
STRING, INT, BOOL, …
Simple values
Reference data
Another ENTITY (with [] opt.)
Single or multi‑valued, supports recursion
Rich semantics
RELATIONSHIP definitions
Edge can carry its own properties



