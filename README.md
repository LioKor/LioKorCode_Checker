### Docker setup on a new server (Ubuntu 22.04 LTS):
1. sudo apt update && sudo apt install apt-transport-https ca-certificates curl software-properties-common
2. curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
3. sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu jammy stable"
4. sudo apt update && sudo apt install docker-ce nginx
5. sudo rm /etc/nginx/sites-enabled/default
6. sudo nano /etc/nginx/sites-available/liokor_code_checker
7. *paste nginx.config into opened file*
8. ln -s /etc/nginx/sites-available/liokor_code_checker /etc/nginx/sites-enabled/liokor_code_checker
9. sudo service nginx restart
10. sudo adduser liokor 
11. sudo usermod -aG docker $USER 
12. sudo apt install python3-pip 
13. pip3 install uwsgi 
14. sudo su liokor && cd ~
15. git clone https://github.com/LioKor/LioKorEdu_Checker.git
16. cd LioKorEdu_Checker 
17. pip3 install -r requirements.txt 
18. docker build -t liokorcode_checker .

### Docker commands
* docker ps
* docker ps -a
* docker rm $(docker ps --filter status=exited -q)
* docker kill UID
* docker stop UID