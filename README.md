
# Twitter Data Analysis Service

## Introduction

Welcome to the Twitter Data Analysis Service! This project was developed as part of a coding challenge to create a web service for analyzing Twitter data. The service allows users to perform various queries on Twitter data, including user recommendations based on interactions.

## Features

- **RESTful API**: Handles HTTP GET requests and provides suitable responses.
- **Data Storage**: Uses PostgreSQL for efficient data storage and retrieval.
- **ETL Process**: Extracts, transforms, and loads data from a JSON file into the database.
- **User Recommendation**: Recommends users based on Twitter interactions, phrases, and hashtags.

## Installation

### Prerequisites

- Python
- Django
- Django REST Framework
- PostgreSQL

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/twitter-data-analysis-service.git
   cd twitter-data-analysis-service
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Ensure the dataset is in the `datasets` folder.

6. Load the initial data:
   ```
   py .\manage.py load_tweets
   ```

## Usage

To run the development server:
```
python manage.py runserver
```

## Endpoints

### Query and User Recommendation

- **Endpoint**: `http://localhost:8000/api/q2`
- **Method**: GET
- **Parameters**:
  - `user_id`: ID of the user to get recommendations for.
  - `type`: Type of interaction (reply, retweet, or both).
  - `phrase`: Phrase to search within tweets.
  - `hashtag`: Hashtag to filter tweets.
- **Response**: A list of recommended users with their latest tweet details.

- **Endpoint**: `http://localhost:8000/api/user-recommendations`
- **Method**: GET
- **Parameters**:
  - `user_id`: ID of the user to get recommendations for.
  - `type`: Type of interaction (reply, retweet, or both).
  - `phrase`: Phrase to search within tweets.
  - `hashtag`: Hashtag to filter tweets.
- **Response**: Get user recommendations based on Twitter interactions.

Example:
```
GET /q2?user_id=10000123&type=retweet&phrase=hello%20cc&hashtag=rwa
```

## Database Schema

- **User**: Stores user information.
- **Tweet**: Stores tweet details including content, hashtags, URLs, and user mentions.
- **Hashtag**: Stores hashtags associated with tweets.
- **URL**: Stores URLs included in tweets.
- **UserMention**: Stores user mentions in tweets.
- **Symbol**: Stores symbols included in tweets.

## ETL Process

The ETL (Extract, Transform, Load) process involves loading the Twitter dataset into the database. It consists of the following steps:

1. **Extract**: Load data from the JSON file.
2. **Transform**: Process and clean the data.
3. **Load**: Insert the data into the database.

Run the ETL process with:
```
py .\manage.py load_tweets
```

## Recommendation System

The recommendation system provides user recommendations based on interactions, phrases, and hashtags. The ranking algorithm consists of three parts:

1. **Interaction Score**: Based on the frequency of replies and retweets.
2. **Hashtag Score**: Based on common hashtags.
3. **Keywords Score**: Based on the occurrence of the given phrase and hashtag.

The final ranking score is calculated as:
```
final_score = interaction_score * hashtag_score * keywords_score
```

## Testing

To run the tests:
```
python manage.py test
```

## Future Improvements

- Optimize query performance for large datasets.

## License

This project is licensed under the MIT License
