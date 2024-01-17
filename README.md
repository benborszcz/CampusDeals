# CampusDeals

Welcome to the CampusDeals repository! This project is designed to help users find and submit deals on campus. To get started with the project on your local machine, please follow the instructions below.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- You have installed Python 3.8 or higher.
- You have installed `pip` for package management.
- You have access to the repository secrets for configuration files.

## Local Setup

To set up the CampusDeals project on your local machine, follow these steps:

1. Clone the repository to your local machine:
   ```sh
   git clone https://github.com/your-username/CampusDeals.git
   cd CampusDeals
   ```

2. Install the required Python packages using `pip`:
   ```sh
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory of the project. This file will store environment variables required for the application to run. Add the following content to the file:
   ```sh
   ELASTICSEARCH_BONSAI_URL=your_elasticsearch_bonsai_url_here
   # Optional: If you want to use the submit deal feature
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   - `ELASTICSEARCH_BONSAI_URL` is provided in the slack.
   - `OPENAI_API_KEY` is optional and must be obtained from OpenAI if you wish to use the submit deal feature.

4. Obtain the `firebase_service_account.json` file from the slack and place it under the `app` folder.

5. Run the Flask application:
   ```sh
   python run.py
   ```

   The application should now be running on `http://localhost:5000`.

## Usage

Once the application is running, you can access the following features:

- **Home Page**: Displays popular deals and includes a search bar for finding deals.
- **Submit Deal**: Allows users to submit new deals. Requires an `OPENAI_API_KEY` to parse deal submissions.
- **Search**: Users can search for deals using keywords.
- **Deal Details**: View detailed information about a specific deal.

## Additional Information

- The application uses Elasticsearch for indexing and searching deals. The configuration for Elasticsearch is specified in the `.env` file.
- Firebase Firestore is used for storing deal data. The `firebase_service_account.json` file is required for authentication.
- The OpenAI API is used for parsing deal submissions into structured data. If you wish to use this feature, you must provide your own `OPENAI_API_KEY` in the `.env` file.

## Contributing

To contribute to the CampusDeals project, please follow these steps:

1. **Create an Issue**: Before starting work on a new feature or fix, create an issue in the GitHub repository describing the change you propose to make. This helps to avoid duplicate efforts and allows for discussion before any code is written.

2. **Branch from Issue**: Once your issue has been created and discussed, create a new branch from the `dev` branch with a name that reflects the issue you're working on. For example, if your issue is number 42 and it's about adding a new search filter, you might name your branch `feature/add-search-filter-42`.

3. **Develop Your Feature**: Make your changes on your new branch. Be sure to keep your code clean and well-documented.

4. **Pull Request**: After you've completed your work and tested it locally, push your branch to the GitHub repository and create a pull request targeting the `dev` branch. Link the pull request to the issue you created in step 1.

5. **Code Review**: Your pull request will be reviewed by other team members. Be open to feedback and make any necessary changes. Once your pull request has been approved, it will be merged into the `dev` branch.

6. **Merging to Main**: Periodically, after thorough testing and review, changes from the `dev` branch will be merged into the `main` branch, which is the production branch.

Please note that both the `main` and `dev` branches are protected. Direct pushes to these branches are not allowed, and all changes must go through the pull request process described above.
