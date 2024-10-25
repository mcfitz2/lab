# specify the node base image with your desired version node:<version>
FROM node:18
# replace this with your application's default port
EXPOSE 4003
RUN mkdir -p /opt/app
WORKDIR /opt/app
COPY ./uptime-service/package.json ./
RUN npm install
COPY ./uptime-service .
CMD [ "npm", "start"]
