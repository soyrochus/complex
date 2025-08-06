// Sample queries for the Complex DSL
// Run schema.dsl and data.dsl first before running this file

// Query 0: Get all nodes in the graph (useful for exploration)
MATCH (n) RETURN n;

// Query 1: Find all employees in Engineering department
MATCH (e:Employee)
WHERE e.department = "Engineering"
RETURN e.name, e.email, e.salary;

// Query 2: Find all epics being worked on and their assignees
MATCH (e:Employee)-[w:WORKS_ON]->(epic:Epic)
RETURN e.name, epic.name, w.role, w.allocation_percent;

// Query 3: Find all documents authored by employees in Engineering
MATCH (emp:Employee)-[:AUTHORED]->(doc:Document)
WHERE emp.department = "Engineering"
RETURN emp.name, doc.title, doc.created_date;

// Query 4: Find high-priority epics with their project assignments
MATCH (epic:Epic)-[p:PART_OF]->(project:Project)
WHERE epic.priority = 1
RETURN epic.name, epic.status, project.name, p.priority_order;

// Query 5: Find all management relationships
MATCH (manager:Employee)-[m:MANAGES]->(employee:Employee)
RETURN manager.name, employee.name, m.management_type, m.start_date;

// Query 6: Find employees working on multiple epics
MATCH (e:Employee)-[:WORKS_ON]->(epic:Epic)
RETURN e.name, e.department;

// Query 7: Find all active employees with their work assignments
MATCH (e:Employee)-[w:WORKS_ON]->(epic:Epic)
WHERE e.active = TRUE
RETURN e.name, e.department, epic.name, w.role;

// Query 8: Find all documents with their tags
MATCH (doc:Document)
RETURN doc.title, doc.tags, doc.created_date;

// Query 9: Find employees by salary range
MATCH (e:Employee)
WHERE e.salary > 90000.0
RETURN e.name, e.department, e.salary;

// Query 10: Find epics in progress with estimated hours
MATCH (epic:Epic)
WHERE epic.status = "In Progress"
RETURN epic.name, epic.estimated_hours, epic.priority;
