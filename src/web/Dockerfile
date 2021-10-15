FROM node:13-alpine as develop-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY ./ .

FROM develop-stage as build-stage
RUN npm run build