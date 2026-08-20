Don't forget to install Docker and Docker compose.

If you are running in Ubuntu(Linux),
1. Clone in folder
2. cd to the folder
3. touch filebrowser.db
4. chmod +x manage.sh
5. run manage.sh

Or if you are running in Windows(wsl),
1. Clone in folder
2. Add filebrowser.db(Empty file)
3. Open terminal inside of the folder
4. Run "docker compose -f core_network.yml up -d"
5. Run "docker compose -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-service.yml up -d"

Also Record your voice and Name it "master.wav".
Save it inside of voice_data folder.

This project is for making little home server which includes :
    filebrowser,
    ollama with openwebui,
    voice check for safety,
    plex,
    nginx proxy service.


If you want to set this server as one-click-service,
1. nano ~server-folder/auto_start.sh
2. copy&paste script:
cd ~server-folder/
export MASTER_PASSWORD="your_default_password"
if [ ! -f .env ]; then
    echo "MASTER_PASSWORD=$MASTER_PASSWORD" > .env
fi
docker network create nas_core_net 2>/dev/null
docker compose -f core_network.yml -f docker-compose-infra.yml -f docker-compose-ai.yml -f docker-compose-user.yml -f docker-compose-service.yml up -d
3. chmode +x ~server-folder/auto_start.sh
4. sudo nano /etc/systemd/system/nas-server.service
5. copy&paste script :
[Unit]
Description=My Mini PC NAS and AI Server Automatic Boot Setup
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=your_user_name
WorkingDirectory=~server-folder
ExecStart=~server-folder//auto_start.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
6. sudo systemctl daemon-reload
7. sudo systemctl enable nas-server.service