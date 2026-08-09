-- ============================================================
-- Auction System Database Schema
-- For use with XAMPP (MySQL/MariaDB) + phpMyAdmin
--
-- Import via phpMyAdmin:
--   1. Start Apache + MySQL in XAMPP Control Panel
--   2. Open http://localhost/phpmyadmin
--   3. Click "Import" -> choose this file -> Go
--
-- Or via command line:
--   C:\xampp\mysql\bin\mysql.exe -u root -p < auction_db.sql
--
-- Default login credentials (password for all: password123):
--   Admin:  admin@auction.com  / password123
--   Seller: john@email.com    / password123
--   Buyer:  jane@email.com    / password123
-- ============================================================

CREATE DATABASE IF NOT EXISTS `auction_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `auction_db`;

-- ------------------------------------------------------------
-- Table: users
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `watchlist`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `bids`;
DROP TABLE IF EXISTS `auction_images`;
DROP TABLE IF EXISTS `auctions`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL,
    `phone` VARCHAR(20),
    `user_type` VARCHAR(20) DEFAULT 'buyer',
    `profile_image` VARCHAR(255),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table: auctions
-- ------------------------------------------------------------
CREATE TABLE `auctions` (
    `auction_id` INT AUTO_INCREMENT PRIMARY KEY,
    `seller_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `category` VARCHAR(100),
    `starting_price` DECIMAL(10,2) NOT NULL,
    `current_price` DECIMAL(10,2) NOT NULL,
    `min_bid_increment` DECIMAL(10,2) DEFAULT 1.00,
    `start_date` DATETIME,
    `end_date` DATETIME,
    `status` VARCHAR(20) DEFAULT 'draft',
    `total_bids` INT DEFAULT 0,
    `winner_id` INT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_auctions_seller` FOREIGN KEY (`seller_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_auctions_winner` FOREIGN KEY (`winner_id`) REFERENCES `users`(`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table: auction_images
-- ------------------------------------------------------------
CREATE TABLE `auction_images` (
    `image_id` INT AUTO_INCREMENT PRIMARY KEY,
    `auction_id` INT NOT NULL,
    `image_url` VARCHAR(255) NOT NULL,
    `is_primary` BOOLEAN DEFAULT FALSE,
    `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_images_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions`(`auction_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table: bids
-- ------------------------------------------------------------
CREATE TABLE `bids` (
    `bid_id` INT AUTO_INCREMENT PRIMARY KEY,
    `auction_id` INT NOT NULL,
    `bidder_id` INT NOT NULL,
    `bid_amount` DECIMAL(10,2) NOT NULL,
    `bid_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `is_auto_bid` BOOLEAN DEFAULT FALSE,
    CONSTRAINT `fk_bids_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions`(`auction_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bids_bidder` FOREIGN KEY (`bidder_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table: payments
-- ------------------------------------------------------------
CREATE TABLE `payments` (
    `payment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `auction_id` INT NOT NULL,
    `buyer_id` INT NOT NULL,
    `seller_id` INT NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `payment_method` VARCHAR(50) DEFAULT 'credit_card',
    `shipping_address` TEXT,
    `payment_status` VARCHAR(20) DEFAULT 'pending',
    `payment_date` DATETIME,
    `transaction_id` VARCHAR(100),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_payments_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions`(`auction_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payments_buyer` FOREIGN KEY (`buyer_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payments_seller` FOREIGN KEY (`seller_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table: watchlist
-- ------------------------------------------------------------
CREATE TABLE `watchlist` (
    `watchlist_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `auction_id` INT NOT NULL,
    `added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_watchlist_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_watchlist_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions`(`auction_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Default accounts (password for all accounts: password123)
-- Hash generated with werkzeug.security.generate_password_hash
-- (scrypt), matching the hashing used by app.py / database_ops.py
-- ------------------------------------------------------------
INSERT INTO `users`
    (`username`, `email`, `password`, `first_name`, `last_name`, `phone`, `user_type`)
VALUES
    ('admin', 'admin@auction.com',
     'scrypt:32768:8:1$9S2L3kEGuiFAfjgQ$e2d14cc60165bd3d57e2975f1fba2ff6000403183197191cbdbd5c157c5a463f5ad33dd5b0ed7d7dbf5ddf200d0972bcc7c303570ec3493b5bf0ea7ca858fc88',
     'System', 'Admin', '', 'admin'),
    ('john', 'john@email.com',
     'scrypt:32768:8:1$9S2L3kEGuiFAfjgQ$e2d14cc60165bd3d57e2975f1fba2ff6000403183197191cbdbd5c157c5a463f5ad33dd5b0ed7d7dbf5ddf200d0972bcc7c303570ec3493b5bf0ea7ca858fc88',
     'John', 'Seller', '', 'seller'),
    ('jane', 'jane@email.com',
     'scrypt:32768:8:1$9S2L3kEGuiFAfjgQ$e2d14cc60165bd3d57e2975f1fba2ff6000403183197191cbdbd5c157c5a463f5ad33dd5b0ed7d7dbf5ddf200d0972bcc7c303570ec3493b5bf0ea7ca858fc88',
     'Jane', 'Buyer', '', 'buyer');
