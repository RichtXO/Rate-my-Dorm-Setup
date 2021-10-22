FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM bunkerity/bunkerized-nginx:1.2.8 as production-stage
COPY --from=build-stage /app/dist /www
