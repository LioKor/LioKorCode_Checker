API_KEY = 'secret_key_here'

# default timeouts in seconds (java requires a lot of time)
DEFAULT_BUILD_TIMEOUT = 4
DEFAULT_TEST_TIMEOUT = 1

# maximum allowed timeouts in seconds
MAX_BUILD_TIMEOUT = 10
# be advised that MAX_TESTING_TIMEOUT means that TEST_TIMEOUT * len(tests) < MAX_TESTING_TIMEOUT
# the default setting means that 32 tests each one for 1 second maximum are allowed
MAX_TESTING_TIMEOUT = 32
