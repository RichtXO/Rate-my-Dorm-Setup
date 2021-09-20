FROM node:lts-alpine

WORKDIR /app

RUN npm install @vue/cli@4.5.13 -g

COPY package.json .
COPY package-lock.json .
RUN npm install

CMD ["npm", "run", "serve"]