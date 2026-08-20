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

This porject is for making little home server which includes,
filebrowser,
ollama with openwebui,
voice check for safety,
plex.