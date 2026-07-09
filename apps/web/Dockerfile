FROM node:20-alpine

WORKDIR /app

COPY package.json package.json
COPY packages/contracts/package.json packages/contracts/package.json
COPY packages/contracts/tsconfig.json packages/contracts/tsconfig.json
COPY packages/contracts/src packages/contracts/src
COPY apps/web/package.json apps/web/package.json

RUN npm install

COPY apps/web apps/web

WORKDIR /app/apps/web
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]

