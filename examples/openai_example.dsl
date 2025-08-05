-- =========================================================
-- 1. SCHEMA  ----------------------------------------------
-- =========================================================

-- A generic super-type so one relationship can target “any artefact”
ENTITY Artifact { 
    name: STRING                        -- human-readable identifier
};

-- Low-level code units
ENTITY SrcFile EXTENDS Artifact { 
    path: STRING,
    language: STRING
};

ENTITY StoredProc EXTENDS Artifact { 
    schema: STRING                      -- Oracle schema / package
};

-- UI abstraction (e.g. a Swing form, dialog, panel …)
ENTITY UIComponent EXTENDS Artifact {
    ui_type: STRING                     -- 'Form', 'Dialog', etc.
};

-- Documentation at any granularity
ENTITY Document { 
    title: STRING,
    kind: STRING                        -- 'user_manual', 'functional_spec', …
};

-- Architectural views / layers / contexts
ENTITY Architecture { 
    name: STRING,
    layer: STRING                       -- ‘Presentation’, ‘Business’, etc.
};

-- --------------- relationships ---------------------------

-- Java file implements business logic found in a stored procedure
RELATIONSHIP IMPLEMENTS_LOGIC (SrcFile 1 -> StoredProc *);

-- Java source defines (renders) one or more UI components
RELATIONSHIP DEFINES_UI      (SrcFile 1 -> UIComponent *);

-- A generic doc-to-artefact link (works for code, UI, procs …)
RELATIONSHIP DOC_FOR         (Document * -> Artifact *);

-- Map any artefact to exactly one architectural element
RELATIONSHIP ARCH_MAP        (Artifact * -> Architecture 1);

-- =========================================================
-- 2. DATA  -------------------------------------------------
-- =========================================================

-- Architectural layers
INSERT Architecture { name="Order UI",          layer="Presentation" } AS archUI;
INSERT Architecture { name="Order Processing",  layer="Business"      } AS archBiz;

-- Source file & corresponding abstract UI
INSERT SrcFile    { name="OrderForm.java",
                    path="src/com/app/ui/OrderForm.java",
                    language="Java" }                                AS orderFormSrc;

INSERT UIComponent { name="OrderForm",
                     ui_type="Form" }                               AS orderFormUI;

-- Stored procedure that the Java form ultimately calls
INSERT StoredProc { name="SP_CREATE_ORDER", schema="ORDERS" }       AS spCreateOrder;

-- Documentation
INSERT Document   { title="Order Processing Manual",
                    kind="user_manual" }                            AS docManual;

INSERT Document   { title="Order Process Functional Spec",
                    kind="functional_spec" }                        AS docFuncSpec;

-- --------------- connect the dots ------------------------

-- Source ↔ UI ↔ Architecture
CONNECT orderFormSrc - DEFINES_UI -> orderFormUI;
CONNECT orderFormSrc - ARCH_MAP   -> archUI;
CONNECT orderFormUI  - ARCH_MAP   -> archUI;

-- Source ↔ Stored procedure ↔ Architecture
CONNECT orderFormSrc  - IMPLEMENTS_LOGIC -> spCreateOrder;
CONNECT spCreateOrder - ARCH_MAP         -> archBiz;

-- Docs ↔ everything they describe
CONNECT docManual   - DOC_FOR -> orderFormUI;
CONNECT docManual   - DOC_FOR -> orderFormSrc;
CONNECT docFuncSpec - DOC_FOR -> spCreateOrder;

-- =========================================================
-- 3. QUERIES  ---------------------------------------------
-- =========================================================

-- Q1: UI components that belong to the Presentation layer
MATCH (ui:UIComponent)-[:ARCH_MAP]->(a:Architecture {layer="Presentation"})
RETURN ui.name, a.name;

-- Q2: Which Java files invoke which stored procedures?
MATCH (src:SrcFile)-[:IMPLEMENTS_LOGIC]->(sp:StoredProc)
RETURN src.name, sp.name;

-- Q3: All documentation links (who documents what?)
MATCH (doc:Document)-[:DOC_FOR]->(art:Artifact)
RETURN doc.title, art.name;
