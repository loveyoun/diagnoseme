from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
           -- partial unique index (doctor 있는 경우)
           CREATE UNIQUE INDEX IF NOT EXISTS uniq_slot
               ON appointment_slots (hospital_id, doctor_id, start_at, end_at)
               WHERE doctor_id IS NOT NULL;

           -- partial unique index (doctor 없는 경우)
           CREATE UNIQUE INDEX IF NOT EXISTS uniq_slot_without_doctor
               ON appointment_slots (hospital_id, start_at, end_at)
               WHERE doctor_id IS NULL;

           -- exclude constraint (겹침 방지)
           ALTER TABLE appointments
               ADD CONSTRAINT no_overlapping_appointments EXCLUDE USING gist (
      user_id WITH =,
      tstzrange(start_at, end_at) WITH &&
    )
    WHERE (status = 'confirmed'); \
           """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    DROP CONSTRAINT IF EXISTS no_overlapping_appointments ON appointments;

    DROP INDEX IF EXISTS uniq_slot;
    DROP INDEX IF EXISTS uniq_slot_without_doctor;
    """
