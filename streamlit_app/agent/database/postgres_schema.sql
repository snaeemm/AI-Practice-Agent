-- PostgreSQL Schema for RFP Bid Management System
-- Optimized for fast queries with JSONB and proper indexes

-- Drop existing tables if migrating from SQLite
DROP TABLE IF EXISTS bid_history_insights CASCADE;
DROP TABLE IF EXISTS capabilities_match CASCADE;
DROP TABLE IF EXISTS qualification_results CASCADE;
DROP TABLE IF EXISTS rfp_assignments CASCADE;
DROP TABLE IF EXISTS rfp_deliverables CASCADE;
DROP TABLE IF EXISTS rfp_raw_data CASCADE;
DROP TABLE IF EXISTS rfp_extracted_data CASCADE;
DROP TABLE IF EXISTS rfp_documents CASCADE;

-- ======================
-- Core RFP Documents
-- ======================
CREATE TABLE rfp_documents (
    rfp_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    project_title TEXT NOT NULL,
    pdf_path TEXT,
    submission_deadline TIMESTAMP,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'processing' CHECK(status IN ('processing', 'qualified', 'planning', 'submitted', 'won', 'lost', 'declined'))
);

CREATE INDEX idx_rfp_client ON rfp_documents(client_name);
CREATE INDEX idx_rfp_status ON rfp_documents(status);
CREATE INDEX idx_rfp_processed_date ON rfp_documents(processed_date DESC);
CREATE INDEX idx_rfp_updated_date ON rfp_documents(updated_date DESC);

-- ======================
-- Complete RFP Raw Data (JSONB)
-- Stores complete RFPData model for fast access
-- ======================
CREATE TABLE rfp_raw_data (
    id SERIAL PRIMARY KEY,
    rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    rfp_data JSONB NOT NULL,
    raw_document_text TEXT,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_data_rfp_id ON rfp_raw_data(rfp_id);
CREATE INDEX idx_raw_data_updated ON rfp_raw_data(updated_date DESC);
-- GIN index for fast JSONB queries
CREATE INDEX idx_raw_data_jsonb ON rfp_raw_data USING GIN (rfp_data);
-- Specific indexes for commonly queried fields
CREATE INDEX idx_raw_data_client ON rfp_raw_data ((rfp_data->>'client_and_opportunity'));
CREATE INDEX idx_raw_data_value ON rfp_raw_data ((rfp_data->'estimated_contract_value'->>'value'));

-- ======================
-- RFP Deliverables (JSONB Arrays)
-- ======================
CREATE TABLE rfp_deliverables (
    id SERIAL PRIMARY KEY,
    rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    client_and_opportunity TEXT,
    technical_deliverables JSONB NOT NULL DEFAULT '[]'::jsonb,
    commercial_deliverables JSONB NOT NULL DEFAULT '[]'::jsonb,
    deliverables_metadata JSONB,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_deliverables_rfp_id ON rfp_deliverables(rfp_id);
CREATE INDEX idx_deliverables_updated ON rfp_deliverables(updated_date DESC);
-- GIN indexes for fast array element queries
CREATE INDEX idx_deliverables_technical ON rfp_deliverables USING GIN (technical_deliverables);
CREATE INDEX idx_deliverables_commercial ON rfp_deliverables USING GIN (commercial_deliverables);
-- Index for searching by section names
CREATE INDEX idx_deliverables_tech_sections ON rfp_deliverables USING GIN ((technical_deliverables -> 'section'));
CREATE INDEX idx_deliverables_comm_sections ON rfp_deliverables USING GIN ((commercial_deliverables -> 'section'));

-- ======================
-- Assignment Analysis (JSONB)
-- ======================
CREATE TABLE rfp_assignments (
    id SERIAL PRIMARY KEY,
    rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    assignment_report JSONB NOT NULL,
    total_deliverables INTEGER,
    granite_assigned INTEGER,
    partner_assigned INTEGER,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assignments_rfp_id ON rfp_assignments(rfp_id);
CREATE INDEX idx_assignments_updated ON rfp_assignments(updated_date DESC);
CREATE INDEX idx_assignments_report ON rfp_assignments USING GIN (assignment_report);
-- Index for searching assignments by owner
CREATE INDEX idx_assignments_owners ON rfp_assignments USING GIN ((assignment_report -> 'assignments'));
-- Index for counts
CREATE INDEX idx_assignments_granite ON rfp_assignments(granite_assigned);
CREATE INDEX idx_assignments_partner ON rfp_assignments(partner_assigned);

-- ======================
-- Qualification Results (JSONB)
-- ======================
CREATE TABLE qualification_results (
    id SERIAL PRIMARY KEY,
    rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    qualification_report JSONB NOT NULL,
    total_score REAL,
    threshold REAL,
    qualifies BOOLEAN,
    rfp_classification TEXT,
    qualified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qualification_rfp_id ON qualification_results(rfp_id);
CREATE INDEX idx_qualification_decision ON qualification_results(qualifies);
CREATE INDEX idx_qualification_score ON qualification_results(total_score DESC);
CREATE INDEX idx_qualification_updated ON qualification_results(updated_date DESC);
CREATE INDEX idx_qualification_classification ON qualification_results(rfp_classification);
-- GIN index for fast JSONB queries
CREATE INDEX idx_qualification_report ON qualification_results USING GIN (qualification_report);
-- Index for searching analyses
CREATE INDEX idx_qualification_analyses ON qualification_results USING GIN ((qualification_report -> 'analyses'));

-- ======================
-- Capabilities Match (JSONB)
-- ======================
CREATE TABLE capabilities_match (
    id SERIAL PRIMARY KEY,
    rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    matched_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    partner_recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    capability_gaps JSONB NOT NULL DEFAULT '[]'::jsonb,
    match_score REAL,
    match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_capabilities_rfp_id ON capabilities_match(rfp_id);
CREATE INDEX idx_capabilities_score ON capabilities_match(match_score DESC);
CREATE INDEX idx_capabilities_updated ON capabilities_match(updated_date DESC);
CREATE INDEX idx_capabilities_matched ON capabilities_match USING GIN (matched_capabilities);
CREATE INDEX idx_capabilities_partners ON capabilities_match USING GIN (partner_recommendations);

-- ======================
-- Bid History Insights (JSONB)
-- ======================
CREATE TABLE bid_history_insights (
    id SERIAL PRIMARY KEY,
    rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    client_name TEXT NOT NULL,
    industry TEXT,
    outcome TEXT CHECK(outcome IN ('won', 'lost', 'no_bid', 'pending')),
    insight_data JSONB NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_insights_rfp_id ON bid_history_insights(rfp_id);
CREATE INDEX idx_insights_client ON bid_history_insights(client_name);
CREATE INDEX idx_insights_industry ON bid_history_insights(industry);
CREATE INDEX idx_insights_outcome ON bid_history_insights(outcome);
CREATE INDEX idx_insights_created ON bid_history_insights(created_date DESC);
CREATE INDEX idx_insights_updated ON bid_history_insights(updated_date DESC);
CREATE INDEX idx_insights_data ON bid_history_insights USING GIN (insight_data);

-- ======================
-- Triggers for auto-updating updated_date
-- ======================
CREATE OR REPLACE FUNCTION update_updated_date_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_date = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_rfp_documents_updated_date BEFORE UPDATE ON rfp_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

CREATE TRIGGER update_rfp_raw_data_updated_date BEFORE UPDATE ON rfp_raw_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

CREATE TRIGGER update_rfp_deliverables_updated_date BEFORE UPDATE ON rfp_deliverables
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

CREATE TRIGGER update_rfp_assignments_updated_date BEFORE UPDATE ON rfp_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

CREATE TRIGGER update_qualification_results_updated_date BEFORE UPDATE ON qualification_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

CREATE TRIGGER update_capabilities_match_updated_date BEFORE UPDATE ON capabilities_match
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

CREATE TRIGGER update_bid_history_insights_updated_date BEFORE UPDATE ON bid_history_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_date_column();

-- ======================
-- Session Management Tables
-- ======================

-- RFP Users table for multi-user support
CREATE TABLE rfp_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_rfp_users_username ON rfp_users(username);
CREATE INDEX idx_rfp_users_email ON rfp_users(email);
CREATE INDEX idx_rfp_users_last_active ON rfp_users(last_active DESC);

-- RFP Sessions table
CREATE TABLE rfp_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES rfp_users(user_id) ON DELETE CASCADE,
    session_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    session_metadata JSONB DEFAULT '{}'::jsonb,
    active_rfp_id TEXT REFERENCES rfp_documents(rfp_id) ON DELETE SET NULL
);

CREATE INDEX idx_rfp_sessions_user ON rfp_sessions(user_id);
CREATE INDEX idx_rfp_sessions_active ON rfp_sessions(is_active);
CREATE INDEX idx_rfp_sessions_updated ON rfp_sessions(updated_at DESC);
CREATE INDEX idx_rfp_sessions_user_active ON rfp_sessions(user_id, is_active);

-- RFP Messages table for conversation history
CREATE TABLE rfp_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES rfp_sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT,
    tool_name TEXT,
    tool_args JSONB,
    tool_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_metadata JSONB DEFAULT '{}'::jsonb,
    sequence_number INTEGER NOT NULL
);

CREATE INDEX idx_rfp_messages_session ON rfp_messages(session_id, sequence_number);
CREATE INDEX idx_rfp_messages_created ON rfp_messages(created_at DESC);
CREATE INDEX idx_rfp_messages_session_role ON rfp_messages(session_id, role);

-- RFP Session-RFP association (many-to-many)
CREATE TABLE rfp_session_rfps (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES rfp_sessions(session_id) ON DELETE CASCADE,
    rfp_id TEXT REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, rfp_id)
);

CREATE INDEX idx_rfp_session_rfps_session ON rfp_session_rfps(session_id);
CREATE INDEX idx_rfp_session_rfps_rfp ON rfp_session_rfps(rfp_id);

-- Triggers for session management
CREATE OR REPLACE FUNCTION update_last_active_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_active = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_rfp_users_last_active BEFORE UPDATE ON rfp_users
    FOR EACH ROW EXECUTE FUNCTION update_last_active_column();

CREATE TRIGGER update_rfp_sessions_updated_at BEFORE UPDATE ON rfp_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ======================
-- Config Files (JSONB) - For storing capabilities and qualification matrix
-- ======================
CREATE TABLE config_files (
    id SERIAL PRIMARY KEY,
    config_name TEXT UNIQUE NOT NULL,
    config_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_config_name ON config_files(config_name);
CREATE INDEX idx_config_updated ON config_files(updated_at DESC);

CREATE TRIGGER update_config_files_updated_at BEFORE UPDATE ON config_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE config_files IS 'System configuration files stored as JSONB (capabilities, qualification matrix)';

-- ======================
-- RFP Lookup Table (Deduplication)
-- ======================
CREATE TABLE rfp_lookup (
    id SERIAL PRIMARY KEY,
    canonical_rfp_id TEXT NOT NULL REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    client_name_normalized TEXT NOT NULL,
    project_title_normalized TEXT NOT NULL,
    submission_deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_name_normalized, project_title_normalized)
);

CREATE INDEX idx_rfp_lookup_canonical ON rfp_lookup(canonical_rfp_id);
CREATE INDEX idx_rfp_lookup_client ON rfp_lookup(client_name_normalized);
CREATE INDEX idx_rfp_lookup_project ON rfp_lookup(project_title_normalized);
CREATE INDEX idx_rfp_lookup_deadline ON rfp_lookup(submission_deadline);
CREATE INDEX idx_rfp_lookup_updated ON rfp_lookup(updated_at DESC);

CREATE TRIGGER update_rfp_lookup_updated_at BEFORE UPDATE ON rfp_lookup
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE rfp_lookup IS 'Lookup table for preventing duplicate RFP entries by mapping normalized client/project names to canonical RFP IDs';

-- ======================
-- Templates Table (for bid plan templates)
-- ======================
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    template_name TEXT UNIQUE NOT NULL,
    template_data BYTEA NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_name ON templates(template_name);
CREATE INDEX idx_templates_updated ON templates(updated_at DESC);

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE templates IS 'Excel templates stored as binary data for bid plan generation';

-- ======================
-- Generated Files Table (for session-based file downloads)
-- ======================
CREATE TABLE IF NOT EXISTS generated_files (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_data BYTEA NOT NULL,
    rfp_id TEXT REFERENCES rfp_documents(rfp_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    downloaded BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_generated_files_session ON generated_files(session_id);
CREATE INDEX idx_generated_files_rfp ON generated_files(rfp_id);
CREATE INDEX idx_generated_files_created ON generated_files(created_at DESC);

COMMENT ON TABLE generated_files IS 'Temporary storage for generated Excel files with session-based access';

-- ======================
-- Presentations Table
-- ======================
CREATE TABLE IF NOT EXISTS presentations (
    id SERIAL PRIMARY KEY,
    presentation_title TEXT NOT NULL,
    presentation_description TEXT,
    rfp_id TEXT REFERENCES rfp_documents(rfp_id) ON DELETE SET NULL,
    presentation_structure JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(presentation_title)
);

CREATE INDEX idx_presentations_title ON presentations(presentation_title);
CREATE INDEX idx_presentations_rfp_id ON presentations(rfp_id);
CREATE INDEX idx_presentations_updated ON presentations(updated_at DESC);
CREATE INDEX idx_presentations_structure ON presentations USING GIN (presentation_structure);

CREATE TRIGGER update_presentations_updated_at BEFORE UPDATE ON presentations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE presentations IS 'Stores standalone presentations with structured content for Gamma.app import';

-- ======================
-- Comments for documentation
-- ======================
COMMENT ON TABLE rfp_documents IS 'Core RFP document metadata';
COMMENT ON TABLE rfp_raw_data IS 'Complete RFP extraction data stored as JSONB for flexible querying';
COMMENT ON TABLE rfp_deliverables IS 'Technical and commercial deliverables with JSONB arrays for flexible updates';
COMMENT ON TABLE rfp_assignments IS 'Assignment analysis with partner/capability matching';
COMMENT ON TABLE qualification_results IS 'Qualification scoring and decision data';
COMMENT ON TABLE capabilities_match IS 'Capability matching analysis for RFPs';
COMMENT ON TABLE bid_history_insights IS 'Historical bid insights for learning and intelligence';

COMMENT ON TABLE rfp_users IS 'User accounts for multi-user RFP session management';
COMMENT ON TABLE rfp_sessions IS 'User RFP sessions with conversation history';
COMMENT ON TABLE rfp_messages IS 'Chat messages and tool interactions for each RFP session';
COMMENT ON TABLE rfp_session_rfps IS 'Association between RFP sessions and RFPs being worked on';

COMMENT ON INDEX idx_deliverables_technical IS 'GIN index for fast queries on technical deliverables array';
COMMENT ON INDEX idx_qualification_report IS 'GIN index for fast queries on entire qualification report';
COMMENT ON INDEX idx_assignments_report IS 'GIN index for fast queries on assignment report';
COMMENT ON INDEX idx_rfp_messages_session IS 'Fast retrieval of messages in chronological order for an RFP session';
