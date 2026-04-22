from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 1. Partial Unique Index (Doctor ID가 있는 경우)
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_slot
        ON appointment_slots (hospital_id, doctor_id, start_at, end_at)
        WHERE doctor_id IS NOT NULL;

    -- 2. Partial Unique Index (Doctor ID가 없는 경우)
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_slot_without_doctor
        ON appointment_slots (hospital_id, start_at, end_at)
        WHERE doctor_id IS NULL;

    -- 3. Exclude Constraint (예약 시간 겹침 방지)
    -- 주의: user_id(UUID/INT)와 tstzrange를 함께 쓰려면 btree_gist 확장이 필요합니다.
    ALTER TABLE appointments
        ADD CONSTRAINT no_overlapping_appointments 
        EXCLUDE USING gist (
            user_id WITH =,
            tstzrange(start_at, end_at) WITH &&
        )
        WHERE (status = 'confirmed');

    -- 4. Active Slots Index
    CREATE INDEX IF NOT EXISTS idx_active_slots 
        ON slots (id) 
        WHERE remains > 0 AND is_active = True;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    DROP CONSTRAINT IF EXISTS no_overlapping_appointments ON appointments;

    DROP INDEX IF EXISTS uniq_slot;
    DROP INDEX IF EXISTS uniq_slot_without_doctor;
    """
