DROP DATABASE IF EXISTS Adds;
CREATE DATABASE Adds;
USE Adds;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT, 
    email VARCHAR(50), 
    password VARCHAR(50), 
    username VARCHAR(50) UNIQUE
);
