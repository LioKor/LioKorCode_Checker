### Docker setup on a new server:
* sudo apt install apt-transport-https ca-certificates curl software-properties-common
* curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
* sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
* sudo apt install docker-ce
* docker pull gcc
* usermod -aG docker $USER

### Docker commands
* docker ps
* docker ps -a
* docker rm $(docker ps --filter status=exited -q)
* docker kill UID
* docker stop UID