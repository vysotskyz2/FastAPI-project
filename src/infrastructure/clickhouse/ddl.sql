CREATE DATABASE IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.user_events
(
    user_id Int64,
    email String,
    created DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(created)
ORDER BY (created, user_id);

CREATE TABLE IF NOT EXISTS analytics.transaction_events
(
    event_type String,
    transaction_id Int64,
    user_id Int64,
    currency String,
    amount Decimal(20, 8),
    status String,
    created DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(created)
ORDER BY (created, user_id);
