# GPT-CodeApp

> Short project description

This project is a chat application where users can get their code reviewed by GPT-4. It utilizes a token counter to evaluate the complexity of the input and also has features like code highlighting and a beautiful user interface.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Tests](#tests)
- [License](#license)
- [Questions](#questions)

## Installation

To install necessary dependencies, run the following command:

```bash
cd /frontend
npm install
```

### Install PostgresSQL
1. Install PostgreSQL: 
   - For macOS: `brew install postgresql`
   - For Ubuntu: `sudo apt-get install postgresql`

2. Start the PostgreSQL service:
   - For macOS: `brew services start postgresql`
   - For Ubuntu: `sudo service postgresql start`

3. Create a new database:
   - Open a terminal and run `psql` to enter the PostgreSQL command-line interface.
   - Run the following command to create a new database: `CREATE DATABASE your_database_name;`

4. Create a database user:
   - Run the following command to create a new user: `CREATE USER your_username WITH PASSWORD 'your_password';`
   - Grant privileges to the user for the database: `GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;`

5. Update your application configuration:
   - In your backend code, update the database connection settings to use the database name, username, and password you created.

6. Test the database connection:
   - Restart your application and check if it successfully connects to the PostgreSQL database.

7. Update the README.md file:
   - Add a section to your README.md file with instructions on setting up the PostgreSQL database, including the installation steps, creating the database and user, and updating the application configuration.

Remember to replace `your_database_name`, `your_username`, and `your_password` with your desired values.

## Usage

Please provide instructions and examples for use.

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Tests

Please provide information on how to run tests for your project, if applicable.

## License

Please provide information on the project's license (if any).

## Questions

If you have any questions about the project, please open an issue or contact the project team.

