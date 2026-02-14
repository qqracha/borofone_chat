-- Fix PostgreSQL sequences for all tables
-- Запусти это после импорта данных или если получаешь duplicate key errors

-- === FIX INVITES SEQUENCE ===
SELECT setval(
    pg_get_serial_sequence('invites', 'id'),
    COALESCE((SELECT MAX(id) FROM invites), 0) + 1,
    false
);

-- === FIX USERS SEQUENCE ===
SELECT setval(
    pg_get_serial_sequence('users', 'id'),
    COALESCE((SELECT MAX(id) FROM users), 0) + 1,
    false
);

-- === FIX ROOMS SEQUENCE ===
SELECT setval(
    pg_get_serial_sequence('rooms', 'id'),
    COALESCE((SELECT MAX(id) FROM rooms), 0) + 1,
    false
);

-- === FIX MESSAGES SEQUENCE ===
SELECT setval(
    pg_get_serial_sequence('messages', 'id'),
    COALESCE((SELECT MAX(id) FROM messages), 0) + 1,
    false
);

-- === VERIFY ===
-- Проверь текущие значения sequences
SELECT 
    'invites' as table_name,
    last_value as current_sequence_value,
    (SELECT MAX(id) FROM invites) as max_table_id
FROM invites_id_seq

UNION ALL

SELECT 
    'users' as table_name,
    last_value as current_sequence_value,
    (SELECT MAX(id) FROM users) as max_table_id
FROM users_id_seq

UNION ALL

SELECT 
    'rooms' as table_name,
    last_value as current_sequence_value,
    (SELECT MAX(id) FROM rooms) as max_table_id
FROM rooms_id_seq

UNION ALL

SELECT 
    'messages' as table_name,
    last_value as current_sequence_value,
    (SELECT MAX(id) FROM messages) as max_table_id
FROM messages_id_seq;
