from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "auth_providers" (
    "id" SMALLSERIAL NOT NULL PRIMARY KEY,
    "code" VARCHAR(20) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "cancel_reasons" (
    "id" SMALLSERIAL NOT NULL PRIMARY KEY,
    "code" VARCHAR(50) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "hospitals" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL,
    "address" VARCHAR(255) NOT NULL,
    "phone_number" VARCHAR(20) NOT NULL,
    "is_active" BOOL NOT NULL
);
CREATE TABLE IF NOT EXISTS "doctors" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(30) NOT NULL,
    "specialty" VARCHAR(100),
    "is_active" BOOL NOT NULL,
    "hospital_id" BIGINT NOT NULL REFERENCES "hospitals" ("id") ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS "appointment_slots" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(6) NOT NULL,
    "capacity" INT NOT NULL,
    "remains" INT NOT NULL,
    "start_at" TIMESTAMPTZ NOT NULL,
    "end_at" TIMESTAMPTZ NOT NULL,
    "slot_duration_minutes" INT NOT NULL,
    "is_active" BOOL NOT NULL,
    "doctor_id" BIGINT REFERENCES "doctors" ("id") ON DELETE SET NULL,
    "hospital_id" BIGINT NOT NULL REFERENCES "hospitals" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_appointment_hospita_1b3876" ON "appointment_slots" ("hospital_id", "is_active");
CREATE INDEX IF NOT EXISTS "idx_appointment_type_fb509e" ON "appointment_slots" ("type");
COMMENT ON COLUMN "appointment_slots"."type" IS 'NORMAL: normal\nHOT: hot';
CREATE TABLE IF NOT EXISTS "slot_template" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(6) NOT NULL,
    "capacity" INT NOT NULL,
    "remains" INT NOT NULL,
    "start_at" TIMESTAMPTZ NOT NULL,
    "end_at" TIMESTAMPTZ NOT NULL,
    "slot_duration_minutes" INT NOT NULL,
    "is_active" BOOL NOT NULL
);
COMMENT ON COLUMN "slot_template"."type" IS 'NORMAL: normal\nHOT: hot';
CREATE TABLE IF NOT EXISTS "user_roles" (
    "id" SMALLSERIAL NOT NULL PRIMARY KEY,
    "code" VARCHAR(20) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "users" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "hashed_password" VARCHAR(128) NOT NULL,
    "phone_number" VARCHAR(20) NOT NULL UNIQUE,
    "name" VARCHAR(30) NOT NULL,
    "email" VARCHAR(254) NOT NULL,
    "nickname" VARCHAR(10) NOT NULL UNIQUE,
    "gender" VARCHAR(1) NOT NULL,
    "birthday" VARCHAR(5) NOT NULL,
    "birthyear" VARCHAR(4) NOT NULL,
    "profile_image" VARCHAR(255),
    "is_active" BOOL NOT NULL,
    "last_login_at" TIMESTAMPTZ,
    "role_id" SMALLINT NOT NULL REFERENCES "user_roles" ("id") ON DELETE RESTRICT
);
COMMENT ON COLUMN "users"."gender" IS 'M: M\nF: F\nU: U';
CREATE TABLE IF NOT EXISTS "appointments" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "idempotency_key" UUID NOT NULL UNIQUE,
    "start_at" TIMESTAMPTZ NOT NULL,
    "end_at" TIMESTAMPTZ NOT NULL,
    "status" VARCHAR(9) NOT NULL,
    "memo" TEXT,
    "cancelled_at" TIMESTAMPTZ,
    "cancel_reason_id" SMALLINT REFERENCES "cancel_reasons" ("id") ON DELETE SET NULL,
    "cancelled_by_id" BIGINT REFERENCES "users" ("id") ON DELETE RESTRICT,
    "hospital_id" BIGINT NOT NULL REFERENCES "hospitals" ("id") ON DELETE RESTRICT,
    "slot_id" BIGINT NOT NULL REFERENCES "appointment_slots" ("id") ON DELETE RESTRICT,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT,
    CONSTRAINT "uid_appointment_user_id_3af34f" UNIQUE ("user_id", "slot_id")
);
CREATE INDEX IF NOT EXISTS "idx_appointment_user_id_24fb58" ON "appointments" ("user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_appointment_hospita_6959a8" ON "appointments" ("hospital_id", "start_at");
CREATE INDEX IF NOT EXISTS "idx_appointment_slot_id_2fa5a0" ON "appointments" ("slot_id", "status");
COMMENT ON COLUMN "appointments"."status" IS 'CONFIRMED: confirmed\nCANCELLED: cancelled\nNO_SHOW: no_show\nCOMPLETED: completed';
CREATE TABLE IF NOT EXISTS "social_accounts" (
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "deleted_at" TIMESTAMPTZ,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "external_id" VARCHAR(255) NOT NULL,
    "provider_id" SMALLINT NOT NULL REFERENCES "auth_providers" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_social_acco_user_id_070729" UNIQUE ("user_id", "provider_id")
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
