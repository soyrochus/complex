// Sample data insertion for the Complex DSL
// Run schema.dsl first before running this file

INSERT Employee {
    name = "Alice Johnson",
    email = "alice.johnson@company.com",
    department = "Engineering",
    hire_date = "2023-01-15",
    salary = 95000.0,
    active = TRUE
} AS alice;

INSERT Employee {
    name = "Bob Smith",
    email = "bob.smith@company.com",
    department = "Product",
    hire_date = "2022-08-20",
    salary = 88000.0,
    active = TRUE
} AS bob;

INSERT Employee {
    name = "Carol Davis",
    email = "carol.davis@company.com",
    department = "Engineering",
    hire_date = "2021-03-10",
    salary = 110000.0,
    active = TRUE
} AS carol;

INSERT Employee {
    name = "David Wilson",
    email = "david.wilson@company.com",
    department = "Design",
    hire_date = "2023-06-01",
    salary = 75000.0,
    active = FALSE
} AS david;

INSERT Project {
    name = "Mobile App Redesign",
    description = "Complete redesign of the mobile application",
    start_date = "2024-01-01",
    end_date = "2024-06-30",
    budget = 500000.0,
    priority = 1,
    status = "Active",
    estimated_hours = 2000.0
} AS mobile_project;

INSERT Epic {
    name = "User Authentication System",
    description = "Implement secure user login and registration",
    priority = 1,
    status = "In Progress",
    estimated_hours = 120.0
} AS auth_epic;

INSERT Epic {
    name = "Payment Integration",
    description = "Integrate with third-party payment providers",
    priority = 2,
    status = "Planning",
    estimated_hours = 80.0
} AS payment_epic;

INSERT Document {
    title = "API Design Specification",
    content = "Detailed specification for the REST API endpoints",
    created_date = "2024-01-15T10:30:00",
    author = alice,
    tags = ["api", "specification", "backend"]
} AS api_doc;

INSERT Document {
    title = "UI/UX Mockups",
    content = "High-fidelity mockups for the new user interface",
    created_date = "2024-01-20T14:45:00",
    author = david,
    tags = ["design", "ui", "mockups"]
} AS design_doc;

INSERT Document {
    title = "Security Requirements",
    content = "Security considerations and requirements document",
    created_date = "2024-01-10T09:15:00",
    author = carol,
    tags = ["security", "requirements", "compliance"]
} AS security_doc;

// Create relationships
CONNECT alice - WORKS_ON -> auth_epic {
    role = "Lead Developer",
    start_date = "2024-01-01",
    allocation_percent = 80.0
};

CONNECT bob - WORKS_ON -> payment_epic {
    role = "Product Manager",
    start_date = "2024-01-15",
    allocation_percent = 60.0
};

CONNECT carol - WORKS_ON -> auth_epic {
    role = "Senior Engineer",
    start_date = "2024-01-01",
    allocation_percent = 50.0
};

CONNECT david - WORKS_ON -> mobile_project {
    role = "UI Designer",
    start_date = "2024-01-01",
    allocation_percent = 90.0
};

CONNECT alice - AUTHORED -> api_doc {
    created_at = "2024-01-15T10:30:00",
    version = 1
};

CONNECT david - AUTHORED -> design_doc {
    created_at = "2024-01-20T14:45:00",
    version = 1
};

CONNECT carol - AUTHORED -> security_doc {
    created_at = "2024-01-10T09:15:00",
    version = 1
};

CONNECT auth_epic - PART_OF -> mobile_project {
    priority_order = 1
};

CONNECT payment_epic - PART_OF -> mobile_project {
    priority_order = 2
};

CONNECT carol - MANAGES -> alice {
    start_date = "2023-01-15",
    management_type = "Technical Lead"
};

CONNECT carol - MANAGES -> bob {
    start_date = "2023-06-01",
    management_type = "Cross-functional"
};
