// =========================================================
// extended_project.dsl
// Exercises the full canonical grammar (v2)            --
// =========================================================

-- =========================================================
-- 1. SCHEMA
-- =========================================================

// Base artefact so we can link docs generically
ENTITY Artifact { name: STRING };

// Low-level code artefacts
ENTITY SrcFile EXTENDS Artifact {
    path: STRING,
    language: STRING
};

// Oracle stored procedure
ENTITY StoredProc EXTENDS Artifact {
    schema: STRING
};

// Abstract UI description: layout + widgets
ENTITY Layout {
    name: STRING,
    type: STRING,
    widgets: STRING[]
};

// Window entity *post-block* inheritance demo
ENTITY Window {
    title: STRING,
    layout: Layout
} EXTENDS Artifact;                -- EXTENDS after field-block

// Action fired from a window (e.g. Save, Next)
ENTITY WindowAction EXTENDS Artifact {
    action_type: STRING
};

// Higher-level logical objects
ENTITY TransactionScope {
    name: STRING,
    description: STRING
};

ENTITY DatabaseTable EXTENDS Artifact { tablespace: STRING };

// Agile requirement
ENTITY UserStory { id: STRING, description: STRING, priority: INT };

// Docs
ENTITY Document { title: STRING, kind: STRING };

// ---------------- relationships ---------------------------

RELATIONSHIP DEFINES_UI      (SrcFile 1 -> Window *);
RELATIONSHIP TRIGGERS_ACTION (Window 1 -> WindowAction *);
RELATIONSHIP REALIZES        (UserStory 1 -> TransactionScope 1) { status: STRING };
RELATIONSHIP IMPLEMENTS_PROC (TransactionScope 1 -> StoredProc 1) { latency_ms: INT };
RELATIONSHIP ACCESSES_TABLE  (TransactionScope 1 -> DatabaseTable *);
RELATIONSHIP DOCS            (Document * -> Artifact *);
RELATIONSHIP CALLS_EDGE      (SrcFile * -> StoredProc *) { call_type: STRING };

-- =========================================================
-- 2. DATA
-- =========================================================

// ---------- user story -----------------------------------
INSERT UserStory {
    id          = "US-001",
    description = "As a clerk I create customer orders",
    priority    = 5
} AS us1;

// ---------- UI layout & window ---------------------------
INSERT Layout {
    name    = "OrderEntryLayout",
    type    = "Form",
    widgets = ["TextField", "ComboBox", "SaveButton"]
} AS layOrder;

INSERT Window {
    title  = "Order Entry",
    layout = layOrder
} AS winOrder;

// window actions
INSERT WindowAction { name = "Save", action_type = "SAVE_ORDER" } AS actSave;
INSERT WindowAction { name = "Next", action_type = "NEXT_STEP" } AS actNext;

CONNECT winOrder - TRIGGERS_ACTION -> actSave;
CONNECT winOrder - TRIGGERS_ACTION -> actNext;

// ---------- source file & stored proc --------------------
INSERT SrcFile {
    name     = "OrderEntry.java",
    path     = "src/com/app/ui/OrderEntry.java",
    language = "Java"
} AS srcOrder;

INSERT StoredProc {
    name   = "SP_CREATE_ORDER",
    schema = "ORDERS_PKG"
} AS spCreate;

// links
CONNECT srcOrder - DEFINES_UI -> winOrder;

// ---------- transaction scope, DB table, mappings --------
INSERT TransactionScope {
    name        = "CreateOrderTx",
    description = "Creates a customer order atomically"
} AS txOrder;

INSERT DatabaseTable {
    name       = "T_ORDERS",
    tablespace = "DATA_TS"
} AS tblOrders;

CONNECT us1     - REALIZES        -> txOrder { status = "Approved" };
CONNECT txOrder - IMPLEMENTS_PROC -> spCreate { latency_ms = 35 };
CONNECT txOrder - ACCESSES_TABLE  -> tblOrders;

// direct call edge with property + edge alias capture later
CONNECT srcOrder - CALLS_EDGE -> spCreate { call_type = "sync" };

// ---------- documentation --------------------------------
INSERT Document { title = "Order Entry UI Manual", kind = "manual" } AS docManual;
CONNECT docManual - DOCS -> winOrder;

// =========================================================
// 3. QUERIES  (act as tests / assertions)
// =========================================================

// Q1: high-priority user stories (>=) and their transaction
MATCH (us:UserStory)-[:REALIZES]->(tx:TransactionScope)
WHERE us.priority >= 4
RETURN us.id, tx.name;

// Q2: windows whose layout is a "Form"
MATCH (w:Window)-[:]->(l:Layout)
WHERE l.type = "Form"
RETURN w.title, l.widgets;

// Q3: edge alias capture & property filter
MATCH (src:SrcFile)-[c:CALLS_EDGE]->(sp:StoredProc)
WHERE c.call_type = "sync"
RETURN src.path, sp.name, c.call_type;

// Q4: latency threshold (> operator on edge property)
MATCH (tx:TransactionScope)-[impl:IMPLEMENTS_PROC]->(sp:StoredProc)
WHERE impl.latency_ms > 30
RETURN tx.name, sp.name, impl.latency_ms;

// Q5: update demo — set transaction description
UPDATE txOrder SET description = "Creates a customer order with validation";

// Q6: delete demo — remove the 'Next' action
MATCH (a:WindowAction { name = "Next" }) DELETE a;
