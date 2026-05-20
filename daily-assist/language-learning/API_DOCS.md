# Language Learning App - API Documentation

This document describes the REST API endpoints available in the backend, including their expected request bodies and response structures.

**Base URL:** `http://127.0.0.1:8000` (when running locally)

---

## 1. Flashcards

These endpoints manage the daily review sessions.

### `GET /flashcards/`
Fetches the 10 words selected for today's review session based on the spaced repetition algorithm.

*   **Response:** `200 OK`
*   **Body Structure:**
    ```json
    {
      "date": "2024-05-20",
      "words": [
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "german_word": "der Hinterhalt",
          "meaning": "ambush",
          "notes": "noun"
        },
        // ... up to 10 words
      ]
    }
    ```

### `POST /flashcards/view`
Records that a user has reviewed a flashcard and logs their confidence score.

*   **Request Body:**
    ```json
    {
      "word_id": "123e4567-e89b-12d3-a456-426614174000",
      "confidence": 4  // Integer between 1 and 5
    }
    ```
*   **Response:** `201 Created`
*   **Body Structure:**
    ```json
    {
      "word_id": "123e4567-e89b-12d3-a456-426614174000",
      "viewed_at": "2024-05-20T14:32:01.123456Z"
    }
    ```

---

## 2. Words

Endpoints for managing the vocabulary.

### `POST /words/`
Adds a new word to the database. The word will initially have an `enrichment_status` of `pending` until the nightly background job fetches examples for it.

*   **Request Body:**
    ```json
    {
      "german_word": "die Geselligkeit",
      "meaning": "sociability",   // Optional
      "notes": "noun"             // Optional
    }
    ```
*   **Response:** `201 Created`
*   **Body Structure:**
    ```json
    {
      "german_word": "die Geselligkeit",
      "meaning": "sociability",
      "notes": "noun",
      "id": "987fcdeb-51a2-43d7-9012-345678901234",
      "enrichment_status": "pending",
      "created_at": "2024-05-20T14:35:00.000000Z"
    }
    ```
*   **Error Responses:**
    *   `409 Conflict`: If the word already exists in the database.

---

## 3. Examples

Endpoints for fetching AI-generated example sentences.

### `GET /words/{word_id}/examples`
Fetches the 10 example sentences generated for a specific word.

*   **Path Parameter:**
    *   `word_id`: The UUID of the word.
*   **Response:** `200 OK`
*   **Body Structure:**
    ```json
    {
      "word_id": "123e4567-e89b-12d3-a456-426614174000",
      "german_word": "schmeicheln",
      "sentences": [
        {
          "sentence_de": "Ich muss ihm schmeicheln, um den Job zu bekommen.",
          "sentence_en": "I have to flatter him to get the job."
        },
        // ... up to 10 sentences
      ]
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If the `word_id` does not exist.

---

## 4. Settings

Endpoints for application-wide configuration.

### `GET /settings/`
Retrieves the current application settings.

*   **Response:** `200 OK`
*   **Body Structure:**
    ```json
    {
      "daily_word_count": 10
    }
    ```

### `PATCH /settings/`
Updates one or more application settings. Note that changes to `daily_word_count` will take effect on the **next calendar day**, as the current day's list is cached.

*   **Request Body:**
    ```json
    {
      "daily_word_count": 15
    }
    ```
*   **Response:** `200 OK`
*   **Body Structure:**
    ```json
    {
      "daily_word_count": 15
    }
    ```
*   **Error Responses:**
    *   `422 Unprocessable Entity`: If `daily_word_count` is not a positive integer.

---

## 5. System

### `GET /health`
A simple health check endpoint to verify the API is running.

*   **Response:** `200 OK`
*   **Body Structure:**
    ```json
    {
      "status": "ok"
    }
    ```
