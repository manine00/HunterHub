-- init.sql

-- 1. Jobs Table (Stores the raw scraped data)
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'Scraped', -- e.g., Scraped, Applied, Interview, Rejected, Accepted
    date_posted DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CV Blocks Table (Stores your modular resume text)
CREATE TABLE IF NOT EXISTS cv_blocks (
    id SERIAL PRIMARY KEY,
    block_name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tags Table (Stores skills/keywords like 'Java', 'Angular', 'Remote')
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- 4. Mapping Table: Jobs <-> Tags
CREATE TABLE IF NOT EXISTS job_tags (
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, tag_id)
);

-- 5. Mapping Table: CV Blocks <-> Tags (So we know which blocks match which job tags)
CREATE TABLE IF NOT EXISTS block_tags (
    block_id INTEGER REFERENCES cv_blocks(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (block_id, tag_id)
);