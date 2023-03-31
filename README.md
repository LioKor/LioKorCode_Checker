# LioKor Code Checker

Service for checking arbitrary code in Docker container using predefined tests. 
Written in python3. Uses dockerpy to control Docker containers and Flask to receive check requests.

## Quick start
1. Build image for running user code: `docker build -t liokorcode_checker liokorcode_checker_image`
2. Build image with checker service: `docker build -t liokorcode_checker_service .`
3. Start checker service: `docker run -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock -ti liokorcode_checker_service`

## Setup without Docker (Ubuntu 22.04 LTS, as root):

### Install required programs:
1. `apt update && apt install apt-transport-https ca-certificates curl software-properties-common`
2. `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -`
3. `add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu jammy stable"`
4. `apt update && apt install build-essential docker-ce nginx python3-pip python3-dev`
5. `pip3 install uwsgi`

### Create and setup "liokor" user:
1. `adduser liokor`
2. `usermod -aG docker liokor`
3. `su liokor && cd ~`
4. `git clone https://github.com/LioKor/LioKorEdu_Checker.git`
5. `cd LioKorEdu_Checker`
6. `pip3 install -r requirements/prod.txt`
7. `cp config.template.py config.py && nano config.py`
8. `docker build -t liokorcode_checker liokorcode_checker_image`
9. `exit`

### Setup service
1. `cp /home/liokor/LioKorEdu_Checker/system_configs/liokor_code_checker.service /etc/systemd/system/`
2. `systemctl enable liokor_code_checker`
3. `service liokor_code_checker start`

### Setup nginx:
1. `rm /etc/nginx/sites-enabled/default`
2. `cp /home/liokor/LioKorEdu_Checker/system_configs/nginx.config /etc/nginx/sites-available/liokor_code_checker`
3. `ln -s /etc/nginx/sites-available/liokor_code_checker /etc/nginx/sites-enabled/liokor_code_checker`
4. `service nginx restart`

### Setup balancer (if needed):
1. `cp /home/liokor/LioKorEdu_Checker/system_configs/nginx_balancer.config /etc/nginx/sites-available/liokor_code_checker_balancer`
2. `nano /etc/nginx/sites-available/liokor_code_checker_balancer`
3. `ln -s /etc/nginx/sites-available/liokor_code_checker_balancer /etc/nginx/sites-enabled/liokor_code_checker_balancer`
4. `service nginx restart`


## Development

### Prepare environment
1. `pip3 install -r requirements/prod.txt`
2. `pip3 install -r requirements/dev.txt`
3. `docker build -t liokorcode_checker liokorcode_checker_image`

### Format code, lint and check types
1. `./format_lint_and_check_types.sh`

### Test
1. `python3 -m unittest`
