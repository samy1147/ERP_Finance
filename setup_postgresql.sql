-- PostgreSQL Database Setup Script
-- Run this in psql or pgAdmin after installing PostgreSQL

-- Step 1: Create the database
CREATE DATABASE finance_erp;

-- Step 2: Create a dedicated user with password
CREATE USER finance_user WITH PASSWORD 'your_secure_password_here';

-- Step 3: Grant privileges to the user
GRANT ALL PRIVILEGES ON DATABASE finance_erp TO finance_user;

-- Step 4: Connect to the database and grant schema privileges
\c finance_erp

-- Grant privileges on schema (PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO finance_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finance_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finance_user;

-- Make future objects accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO finance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO finance_user;

-- Verify the setup
\l finance_erp
\du finance_user

-- Done! You can now exit psql and continue with Django setup
