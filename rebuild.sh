echo " ---- Redeploying RPM -----"
echo " ---- Pulling latest changes from Git ----- "
git pull origin dev
echo " ---- Removing old images ----- "
docker-compose down
echo " ---- Building new images ----- "
docker-compose up --build -d
echo " ---- RPM rebuild complete. ----- "
echo "----- Enjoy latest changes -----"