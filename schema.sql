-- schema.sql

CREATE TABLE users (
    userID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE products (
    productID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    cost REAL,
    price REAL,
    category TEXT
);

CREATE TABLE warehouses (
    warehouseID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT
);

CREATE TABLE inventory (
    inventoryID INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouseID INTEGER,
    productID INTEGER,
    quantity INTEGER,
    FOREIGN KEY (warehouseID) REFERENCES warehouses(warehouseID),
    FOREIGN KEY (productID) REFERENCES products(productID)
);

CREATE TABLE logs (
    logID INTEGER PRIMARY KEY AUTOINCREMENT,
    userID INTEGER,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES users(userID)
);
