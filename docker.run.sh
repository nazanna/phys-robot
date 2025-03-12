sudo docker build --build-arg TEST='False' -t physbot_image --secret id=yc_key,src=./secrets/authorized_key.json .
# Prod:
sudo docker run --name physbot -d --volume phys_bot_data:/app/data physbot_image
# For testing:
# sudo docker run --name physbot --rm --volume phys_bot_data:/app/data -it physbot_image bash