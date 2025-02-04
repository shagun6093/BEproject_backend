# Flask API Testing Guide (Thunder Client)

This guide explains how to test the Flask API using **Thunder Client**, a REST API client for VS Code. Follow the steps below to test each API endpoint.

## Prerequisites

- Install **Thunder Client** in VS Code.
- Ensure **MongoDB** is running (`mongodb://localhost:27017/`).
- Install required Python dependencies using:
  ```bash
  pip install flask pymongo bcrypt pyjwt python-dotenv
  ```
- Start the Flask API:
  ```bash
  python api.py
  ```

---

## API Endpoints & Testing

### 1. User Registration

**Endpoint:** `POST /register`

**Request Body:** (JSON)
```json
{
  "name": "John Doe",
  "age": 25,
  "mail": "john@example.com",
  "phonenumber": "1234567890",
  "password": "password123",
  "confirm_password": "password123"
}
```
**Expected Response:**
```json
{
  "message": "User registered successfully"
}
```

---

### 2. User Login

**Endpoint:** `POST /login`

**Request Body:** (JSON)
```json
{
  "mail": "john@example.com",
  "password": "password123"
}
```
**Expected Response:**
```json
{
  "message": "Login successful",
  "token": "<JWT_TOKEN>"
}
```
(Note: Copy the `token` for testing protected routes.)

---

### 3. Dashboard (Authenticated)

**Endpoint:** `GET /dashboard`

**Headers:**
```plaintext
x-access-token: <JWT_TOKEN>
```
**Expected Response:**
```json
{
  "message": "Welcome to the dashboard",
  "user": {
    "name": "John Doe",
    "age": 25,
    "mail": "john@example.com",
    "phonenumber": "1234567890"
  }
}
```

---

### 4. Create Task

**Endpoint:** `POST /create_task`

**Request Body:** (JSON)
```json
{
  "task_name": "Complete Project",
  "user_response": "Pending",
  "task_id": 1
}
```
**Expected Response:**
```json
{
  "message": "Task created",
  "task_id": "<Generated_Task_ID>"
}
```

---

### 5. Update Task

**Endpoint:** `PUT /update_task/1`

**Request Body:** (JSON)
```json
{
  "user_response": "Completed"
}
```
**Expected Response:**
```json
{
  "message": "Task updated successfully"
}
```

---

### 6. Delete Task

**Endpoint:** `DELETE /delete_task/1`

**Expected Response:**
```json
{
  "message": "Task deleted"
}
```

---

## Notes
- Ensure **MongoDB** is running before testing.
- Use the **Thunder Client** extension in VS Code to send HTTP requests.
- For **protected routes**, copy the `token` from the login response and pass it as the `x-access-token` header.

Happy Testing! 🚀

