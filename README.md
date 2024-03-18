# LioKor Code Checker

Service for checking arbitrary code in Docker container using predefined tests. 
Written in python3. Uses dockerpy to control Docker containers and Flask to receive check requests.

## Quick start
1. Build image for running user code: `docker build -t liokorcode_checker liokorcode_checker_image`
2. Build image with checker service: `docker build -t liokorcode_checker_service .`
3. Start checker service: `docker run -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock -ti liokorcode_checker_service`

## Development

### Prepare environment
1. `poetry env use 3.12 && poetry install`
2. `docker build -t liokorcode_checker liokorcode_checker_image`

### Format code, lint and check types
1. `./format_lint_and_check_types.sh`

### Test
1. `python3 -m unittest`
