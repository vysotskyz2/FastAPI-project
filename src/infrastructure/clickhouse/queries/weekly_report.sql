WITH
    week_series AS (
        SELECT subtractWeeks(toMonday(now()), number) AS week
        FROM numbers({weeks:UInt32})
    ),
    rollbacked AS (
        SELECT DISTINCT transaction_id
        FROM analytics.transaction_events
        WHERE event_type = 'ROLLBACKED'
    ),
    txn AS (
        SELECT
            transaction_id,
            any(user_id) AS user_id,
            any(amount) AS amount,
            min(created) AS created
        FROM analytics.transaction_events
        WHERE event_type = 'CREATED'
        GROUP BY transaction_id
    ),
    user_agg AS (
        SELECT
            toMonday(created) AS week,
            count(DISTINCT user_id) AS registered_users_count
        FROM analytics.user_events
        GROUP BY week
    ),
    txn_agg AS (
        SELECT
            toMonday(t.created) AS week,
            count() AS transactions_count,
            countIf(r.transaction_id = 0) AS not_rollbacked_transactions_count,
            sumIf(t.amount, r.transaction_id = 0 AND t.amount > 0) AS not_rollbacked_deposit_amount,
            sumIf(t.amount, r.transaction_id = 0 AND t.amount < 0) AS not_rollbacked_withdraw_amount
        FROM txn AS t
        LEFT JOIN rollbacked AS r ON r.transaction_id = t.transaction_id
        GROUP BY week
    ),
    deposit_users AS (
        SELECT
            toMonday(u.created) AS week,
            count(DISTINCT u.user_id) AS registered_and_deposit_users_count
        FROM analytics.user_events AS u
        INNER JOIN txn AS d
            ON d.user_id = u.user_id
            AND d.amount > 0
            AND toMonday(d.created) = toMonday(u.created)
        GROUP BY week
    ),
    nb_deposit_users AS (
        SELECT
            toMonday(u.created) AS week,
            count(DISTINCT u.user_id) AS registered_and_not_rollbacked_deposit_users_count
        FROM analytics.user_events AS u
        INNER JOIN txn AS d
            ON d.user_id = u.user_id
            AND d.amount > 0
            AND toMonday(d.created) = toMonday(u.created)
        LEFT JOIN rollbacked AS r ON r.transaction_id = d.transaction_id
        WHERE r.transaction_id = 0
        GROUP BY week
    )
SELECT
    ws.week AS week,
    u.registered_users_count,
    du.registered_and_deposit_users_count,
    ndu.registered_and_not_rollbacked_deposit_users_count,
    t.not_rollbacked_deposit_amount,
    t.not_rollbacked_withdraw_amount,
    t.transactions_count,
    t.not_rollbacked_transactions_count
FROM week_series AS ws
LEFT JOIN user_agg AS u ON u.week = ws.week
LEFT JOIN txn_agg AS t ON t.week = ws.week
LEFT JOIN deposit_users AS du ON du.week = ws.week
LEFT JOIN nb_deposit_users AS ndu ON ndu.week = ws.week
ORDER BY ws.week
