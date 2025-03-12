sudo docker build . -t physbot_image --secret id=yc_key,src=./secrets/authorized_key.json
sudo docker run --name physbot --rm --volume sqlite_data:/app/data physbot_image