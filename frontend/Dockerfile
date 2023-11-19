# Use an official Node runtime as a parent image
FROM node:18

# Copy package.json and package-lock.json
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm install

# Bundle app source inside the Docker image
COPY . .

# Choose the port the container will listen on at runtime
EXPOSE 3000

# Run the specified command within the container
CMD [ "npm", "run", "dev" ]
