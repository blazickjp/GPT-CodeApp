# Use an official Node.js runtime as the base image
FROM node:18

# Set the working directory in the container to /app
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm install

# Bundle the app source inside the Docker image
COPY . .

ENV PORT 5000

# Make port 3000 available to the outside world
EXPOSE 5000

# Define the command to run the app
CMD [ "npm", "run", "dev" ]