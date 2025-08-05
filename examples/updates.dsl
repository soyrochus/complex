// Sample update and delete operations for the Complex DSL
// Run schema.dsl and data.dsl first before running this file

// Update operations

// Update an employee's salary and department
UPDATE Employee {name = "Alice Johnson"} SET 
    salary = 105000.0,
    department = "Senior Engineering";

// Update epic status
UPDATE Epic {name = "User Authentication System"} SET 
    status = "Completed",
    estimated_hours = 95.0;

// Update document content
UPDATE Document {title = "API Design Specification"} SET 
    content = "Updated API specification with new endpoints and security requirements";

// Update project end date and budget
UPDATE Project {name = "Mobile App Redesign"} SET 
    end_date = "2024-08-31",
    budget = 550000.0;

// Delete operations

// Delete inactive employees
DELETE Employee {active = FALSE};

// Delete completed epics (be careful with relationships!)
DELETE Epic {status = "Completed"};

// Delete old documents (example - be careful with author relationships!)
// DELETE Document {title = "Old Design Doc"};

// Insert new data after updates

INSERT Employee {
    name = "Eve Martinez",
    email = "eve.martinez@company.com",
    department = "QA",
    hire_date = "2024-02-01",
    salary = 70000.0,
    active = TRUE
} AS eve;

INSERT Epic {
    name = "Quality Assurance Framework",
    description = "Implement automated testing framework",
    priority = 3,
    status = "Planning",
    estimated_hours = 150.0
} AS qa_epic;

// Connect new employee to new epic
CONNECT eve - WORKS_ON -> qa_epic {
    role = "QA Lead",
    start_date = "2024-02-01",
    allocation_percent = 100.0
};

// Update work allocation after organizational changes
UPDATE Employee {name = "Bob Smith"} SET 
    department = "Product Management";

// Connect QA epic to mobile project
CONNECT qa_epic - PART_OF -> mobile_project {
    priority_order = 3
};
