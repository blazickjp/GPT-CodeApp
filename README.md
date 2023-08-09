# GPT-CodeApp

![GitHub stars](https://img.shields.io/github/stars/blazickjp/GPT-CodeApp?style=social) ![GitHub release (latest by date)](https://img.shields.io/github/v/release/blazickjp/GPT-CodeApp) ![GitHub All Releases](https://img.shields.io/github/downloads/blazickjp/GPT-CodeApp/total)

> This project is a clone of Chat-GPT with all the features we wish were available. After getting frustrated by constantly copying and pasting from VS Code into the UI, losing context in the conversation memory, and having little visibility into what's going on under the hood I decided to test the AI's coding ability by making this app. This project started as a tool to better manage the model's conversational memory and context but now we're setting new goals! We're giving the models access to read, write, and edit files but the user has full control! Until these models get better (GPT-5?) we're putting more control in the users hands, but offloading all of the tedious work to the models. This App is very much still a work in progress, but come test it out!

![](images/Snip20230801_3.png)

## Todo

- [x] Testing
- [x] Improve quality of conversation memory
- [x] Edit User Files with LLM
- [x] Give LLM functions to create files and add boiler plate code
- [x] Support Multiple Conversations
- [ ] Support Multiple "Identities" for LLM (debugging, adding feature, refactor, etc...)
- [ ] Better Interface for Adding / Changing LLM Functions
- [ ] Use Wisper to add voice interface
- [ ] User authentication system
- [ ] Comprehensive User Documentation

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [Tests](#tests)
- [License](#license)
- [Questions](#questions)

## Installation

To install necessary dependencies, run the following commands:

### Install PostgresSQL
1. Install PostgreSQL: 
   - For macOS: `brew install postgresql`
   - For Ubuntu: `sudo apt-get install postgresql`

2. Start the PostgreSQL service:
   - For macOS: `brew services start postgresql`
   - For Ubuntu: `sudo service postgresql start`

3. Create a new database:
   - Open a terminal and run `psql` to enter the PostgreSQL command-line interface.
   - If you are prompted for a password, you may need to instead run `psql -U postgres -h localhost` and provide the superuser password you provided at set-up.
   - Run the following command to create a new database: `CREATE DATABASE your_database_name;`

4. Create a database user:
   - Run the following command to create a new user: `CREATE USER your_username WITH PASSWORD 'your_password';`
   - Grant privileges to the user for the database: `GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;`

5. Update your application configuration:
   - Use the example `.env.sample` file in the root to create your own `.env` file. The backend code will find the file automatically for authentication.:
      ```sh
      CCODEAPP_DB_NAME=DB_FROM_SETUP_STEP3
      CODEAPP_DB_USER=USER_FROM_SETUP_STEP4
      CODEAPP_DB_PW=PW_FROM_SETUP_STEP4
      CODEAPP_DB_HOST=localhost
      IGNORE_DIRS=[node_modules,.nextm,.venv,__pycache__,.git]
      FILE_EXTENSIONS=[.js,.py,.md]
      ```
      It is important that if you are using a virtual environment not named `.venv` to add it to the ignored directories.

6. Test the database connection:
   - Restart your application and check if it successfully connects to the PostgreSQL database.

Remember to replace `your_database_name`, `your_username`, and `your_password` with your desired values.

## Usage

```bash
cd /frontend
npm install
npm run dev
```

```bash
cd /backend
uvicorn main:app --reload
```

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

See [Contributing Guide](CONTRIBUTING.md)

## Tests

```bash
cd backend
python3 -m pytest 
```

## Questions

If you have any questions about the project, please open an issue or contact the project team.

