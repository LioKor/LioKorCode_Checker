### Docker setup on a new server:
* sudo apt install apt-transport-https ca-certificates curl software-properties-common
* curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
* sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
* sudo apt update
* sudo apt install docker-ce
* docker pull gcc
* adduser liokor
* usermod -aG docker $USER
* sudo apt install python3-pip
* pip install uwsgi
* sudo su liokor
* git clone git@github.com:LioKor/LioKorEdu_Checker.git
* cd LioKorEdu_Checker
* pip3 install -r requirements.txt

### Docker commands
* docker ps
* docker ps -a
* docker rm $(docker ps --filter status=exited -q)
* docker kill UID
* docker stop UID