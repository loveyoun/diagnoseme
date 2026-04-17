from pydantic import ConfigDict

FROZEN_CONFIG = ConfigDict(frozen=True)
FROZEN_RESPONSE_CONFIG = ConfigDict(frozen=True, from_attributes=True)
