CREATE DATABASE resume_parser;
-- Run the following as a PostgreSQL administrator, then update DATABASE_URL:
CREATE USER resume_user WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE resume_parser TO resume_user;
\connect resume_parser
GRANT ALL ON SCHEMA public TO resume_user;
