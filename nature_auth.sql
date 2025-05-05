-- Active: 1744095484900@@127.0.0.1@3307@nature_auth
-- Create the database
CREATE DATABASE IF NOT EXISTS nature_auth;

-- Use the database
USE nature_auth;

-- Create a users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

