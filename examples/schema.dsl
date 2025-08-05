// Sample schema definition for the Complex DSL
// This demonstrates entity and relationship definitions

ENTITY Employee {
    name: STRING,
    email: STRING,
    department: STRING,
    hire_date: DATE,
    salary: FLOAT,
    active: BOOL
};

ENTITY Document {
    title: STRING,
    content: STRING,
    created_date: DATETIME,
    author: Employee,
    tags: STRING[]
};

ENTITY Epic {
    name: STRING,
    description: STRING,
    priority: INT,
    status: STRING,
    estimated_hours: FLOAT
};

ENTITY Project {
    name: STRING,
    description: STRING,
    start_date: DATE,
    end_date: DATE,
    budget: FLOAT
} EXTENDS Epic;

RELATIONSHIP WORKS_ON (Employee * -> Epic *) {
    role: STRING,
    start_date: DATE,
    allocation_percent: FLOAT
};

RELATIONSHIP AUTHORED (Employee 1 -> Document *) {
    created_at: DATETIME,
    version: INT
};

RELATIONSHIP PART_OF (Epic * -> Project 1) {
    priority_order: INT
};

RELATIONSHIP MANAGES (Employee 1 -> Employee *) {
    start_date: DATE,
    management_type: STRING
};
