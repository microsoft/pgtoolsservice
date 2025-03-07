FROM mcr.microsoft.com/azurelinux/base/nodejs:20
WORKDIR /app
COPY . .
RUN npm install --include=dev
RUN npx webpack

