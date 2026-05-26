-- FastRouter Initial Schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    subscription_status VARCHAR(20) DEFAULT 'inactive',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    free_requests_used INT DEFAULT 0,
    free_requests_limit INT DEFAULT 1000,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Platform API keys
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,
    name VARCHAR(100) DEFAULT 'Default',
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Provider keys (BYOK)
CREATE TABLE IF NOT EXISTS provider_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    api_key_id UUID REFERENCES api_keys(id),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    latency_ms INT,
    cached BOOLEAN DEFAULT FALSE,
    agent_type VARCHAR(20) DEFAULT 'unknown',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_provider ON usage_logs(provider);

-- Provider routing config
CREATE TABLE IF NOT EXISTS provider_configs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model_pattern VARCHAR(100),
    priority INT DEFAULT 0,
    weight INT DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    circuit_breaker_status VARCHAR(20) DEFAULT 'closed',
    failure_count INT DEFAULT 0,
    last_failure_time TIMESTAMPTZ,
    settings JSONB DEFAULT '{}'
);

-- Seed default providers
INSERT INTO provider_configs (provider, model_pattern, priority, weight, settings) VALUES
('deepseek', 'deepseek*', 1, 100, '{"api_base": "https://api.deepseek.com", "context_length": 65536}'),
('qwen', 'qwen*', 2, 80, '{"api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "context_length": 131072}')
ON CONFLICT DO NOTHING;
