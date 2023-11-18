# Warbler

Welcome to My Project! This project allows users create a profile for themselves, follow other users, and create their own messages.  

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)

## Installation

To install and run My Project locally, please follow these steps:  

1. Navigate to desired local project directory:

cd YOUR-DIR  

2. Clone Repository:

https://github.com/vnouaime/Exercise-Pet-Adoption.git  

3. Create venv folder and activate virtual environment:

python3 -m venv venv  
source venv/bin/activate  

4. Install the dependencies from requirements.txt:

pip install -r requirements.txt 

5. Set up flask environment:

export FLASK_ENV=development  
export FLASK_ENV=testing  

6. Start the application:

flask run  

5. Open your web browser and visit `http://localhost:5000` to access My Project.

## Usage

Redirects to register page where user can register and will be redirected to personalized home page. Displays username, number of followers, people you are following, and messages. Users can update and delete their own messages from their page. Can follow other users then home page will personalize to display messages of users that user is following. Users can log out and log in where they are authenticated. Users can delete their own profile as well.  

## Contributing

Contributions are welcome! If you'd like to contribute to My Project, please follow these steps:  

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/my-feature`.
3. Make your changes and commit them: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin feature/my-feature`.
5. Submit a pull request.