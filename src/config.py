from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    API_KEY: str = Field(default=...)

    # default timeouts in seconds (java requires a lot of time)
    DEFAULT_BUILD_TIMEOUT: int = 4
    DEFAULT_TEST_TIMEOUT: int = 1

    # maximum allowed timeouts in seconds
    MAX_BUILD_TIMEOUT: int = 10
    # be advised that MAX_TESTING_TIMEOUT means that TEST_TIMEOUT * len(tests) < MAX_TESTING_TIMEOUT
    # the default setting means that 32 tests each one for 1 second maximum are allowed
    MAX_TESTING_TIMEOUT: int = 32
