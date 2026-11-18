-- CLS-4163: seed the four gift offering reasons, promotion DB, once per environment after the deploy.
-- Brands that already have reasons are skipped, so a rerun inserts nothing.
-- pp1 already has them (seeded by the first version of the migration, 2026-11-02).
INSERT INTO reward_offering_reason (domain_id, name, created_at, updated_at)
SELECT d.domain_id, n.name, NOW(), NOW()
FROM (
    SELECT domain_id FROM player
    UNION SELECT domain_id FROM promotion_configuration
    UNION SELECT domain_id FROM gift
) d
CROSS JOIN (
    SELECT 'Birthday' AS name
    UNION ALL SELECT 'Christmas'
    UNION ALL SELECT 'Easter'
    UNION ALL SELECT 'Valentine''s day'
) n
WHERE d.domain_id NOT IN (SELECT domain_id FROM reward_offering_reason);
