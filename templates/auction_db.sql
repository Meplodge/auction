-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 09, 2026 at 03:12 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `auction_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `auctions`
--

CREATE TABLE `auctions` (
  `auction_id` int(11) NOT NULL,
  `seller_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `starting_price` decimal(10,2) NOT NULL,
  `current_price` decimal(10,2) NOT NULL,
  `min_bid_increment` decimal(10,2) DEFAULT 1.00,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT 'draft',
  `total_bids` int(11) DEFAULT 0,
  `winner_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `auctions`
--

INSERT INTO `auctions` (`auction_id`, `seller_id`, `title`, `description`, `category`, `starting_price`, `current_price`, `min_bid_increment`, `start_date`, `end_date`, `status`, `total_bids`, `winner_id`, `created_at`) VALUES
(1, 2, 'Vintage Rolex Submariner Watch', 'Genuine 1978 Rolex Submariner, recently serviced, comes with original box and papers.', 'Watches', 1500.00, 1800.00, 50.00, '2026-08-07 12:54:32', '2026-08-14 12:54:32', 'active', 4, NULL, '2026-08-09 10:54:32'),
(2, 2, 'Antique Oak Writing Desk', 'Solid oak roll-top desk from the early 1900s, fully restored with working lock.', 'Furniture', 300.00, 460.00, 20.00, '2026-08-08 12:54:32', '2026-08-15 12:54:32', 'active', 4, NULL, '2026-08-09 10:54:32'),
(3, 4, 'Gaming Laptop - RTX 4080, 32GB RAM', 'High-end gaming laptop, barely used, includes charger and original packaging.', 'Electronics', 1200.00, 1475.00, 25.00, '2026-08-06 12:54:32', '2026-08-13 12:54:32', 'active', 5, NULL, '2026-08-09 10:54:32'),
(4, 4, 'Rare Silver Age Comic Book Collection', 'Set of 12 Silver Age comics in protective sleeves, great condition for their age.', 'Collectibles', 500.00, 720.00, 20.00, '2026-07-30 12:54:32', '2026-08-08 12:54:32', 'closed', 4, 3, '2026-08-09 10:54:32'),
(5, 5, 'Trek X-Caliber Mountain Bike', 'Aluminum frame mountain bike, size L, lightly used, well maintained.', 'Sports', 250.00, 300.00, 15.00, '2026-08-08 12:54:32', '2026-08-12 12:54:32', 'active', 2, NULL, '2026-08-09 10:54:32'),
(6, 5, 'Diamond Pendant Necklace, 18k Gold', '1 carat diamond pendant on an 18k gold chain, includes certificate of authenticity.', 'Jewelry', 800.00, 1100.00, 50.00, '2026-08-01 12:54:32', '2026-08-07 12:54:32', 'closed', 4, 6, '2026-08-09 10:54:32'),
(7, 2, 'Fender Stratocaster Electric Guitar', 'Classic Fender Stratocaster in sunburst finish, includes hard case.', 'Musical Instruments', 600.00, 600.00, 25.00, '2026-08-09 12:54:32', '2026-08-16 12:54:32', 'draft', 0, NULL, '2026-08-09 10:54:32'),
(8, 4, 'Original Oil Painting - Countryside Landscape', 'Hand-painted oil on canvas, 60x80cm, framed and ready to hang.', 'Art', 150.00, 190.00, 10.00, '2026-08-05 12:54:32', '2026-08-11 12:54:32', 'active', 3, NULL, '2026-08-09 10:54:32'),
(9, 1, 'cfvghdcghdfhg', 'dfgdgdfg', 'Furniture', 24444.00, 24445.00, 1.00, '2026-08-09 14:24:00', '2026-08-16 14:24:00', 'active', 1, NULL, '2026-08-09 12:24:22');

-- --------------------------------------------------------

--
-- Table structure for table `auction_images`
--

CREATE TABLE `auction_images` (
  `image_id` int(11) NOT NULL,
  `auction_id` int(11) NOT NULL,
  `image_url` varchar(255) NOT NULL,
  `is_primary` tinyint(1) DEFAULT 0,
  `uploaded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `auction_images`
--

INSERT INTO `auction_images` (`image_id`, `auction_id`, `image_url`, `is_primary`, `uploaded_at`) VALUES
(1, 1, 'seed_1_vintage-rolex-submariner-watch_1.jpg', 1, '2026-08-09 11:19:59'),
(2, 1, 'seed_1_vintage-rolex-submariner-watch_2.jpg', 0, '2026-08-09 11:20:49'),
(3, 1, 'seed_1_vintage-rolex-submariner-watch_3.jpg', 0, '2026-08-09 11:21:18'),
(4, 2, 'seed_2_antique-oak-writing-desk_0.jpg', 1, '2026-08-09 11:21:24'),
(5, 2, 'seed_2_antique-oak-writing-desk_1.jpg', 0, '2026-08-09 11:21:28'),
(6, 2, 'seed_2_antique-oak-writing-desk_2.jpg', 0, '2026-08-09 11:21:30'),
(7, 3, 'seed_3_gaming-laptop-rtx-4080-32gb-ram_0.jpg', 1, '2026-08-09 11:21:47'),
(8, 3, 'seed_3_gaming-laptop-rtx-4080-32gb-ram_1.jpg', 0, '2026-08-09 11:21:49'),
(9, 3, 'seed_3_gaming-laptop-rtx-4080-32gb-ram_2.jpg', 0, '2026-08-09 11:21:51'),
(10, 4, 'seed_4_rare-silver-age-comic-book-collection_0.jpg', 1, '2026-08-09 11:21:56'),
(11, 4, 'seed_4_rare-silver-age-comic-book-collection_1.jpg', 0, '2026-08-09 11:21:59'),
(12, 4, 'seed_4_rare-silver-age-comic-book-collection_2.jpg', 0, '2026-08-09 11:22:02'),
(13, 5, 'seed_5_trek-x-caliber-mountain-bike_0.jpg', 1, '2026-08-09 11:22:12'),
(14, 5, 'seed_5_trek-x-caliber-mountain-bike_1.jpg', 0, '2026-08-09 11:22:27'),
(15, 5, 'seed_5_trek-x-caliber-mountain-bike_2.jpg', 0, '2026-08-09 11:23:24'),
(16, 6, 'seed_6_diamond-pendant-necklace-18k-gold_0.jpg', 1, '2026-08-09 11:23:48'),
(17, 6, 'seed_6_diamond-pendant-necklace-18k-gold_1.jpg', 0, '2026-08-09 11:24:03'),
(18, 6, 'seed_6_diamond-pendant-necklace-18k-gold_2.jpg', 0, '2026-08-09 11:24:18'),
(19, 7, 'seed_7_fender-stratocaster-electric-guitar_0.jpg', 1, '2026-08-09 11:24:21'),
(20, 7, 'seed_7_fender-stratocaster-electric-guitar_1.jpg', 0, '2026-08-09 11:24:22'),
(21, 7, 'seed_7_fender-stratocaster-electric-guitar_2.jpg', 0, '2026-08-09 11:24:22'),
(22, 8, 'seed_8_original-oil-painting-countryside-landsc_0.jpg', 1, '2026-08-09 11:24:27'),
(23, 8, 'seed_8_original-oil-painting-countryside-landsc_1.jpg', 0, '2026-08-09 11:24:28'),
(24, 8, 'seed_8_original-oil-painting-countryside-landsc_2.jpg', 0, '2026-08-09 11:24:30'),
(25, 9, '20260809_142422_largeprint.png', 1, '2026-08-09 12:24:22');

-- --------------------------------------------------------

--
-- Table structure for table `bids`
--

CREATE TABLE `bids` (
  `bid_id` int(11) NOT NULL,
  `auction_id` int(11) NOT NULL,
  `bidder_id` int(11) NOT NULL,
  `bid_amount` decimal(10,2) NOT NULL,
  `bid_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `is_auto_bid` tinyint(1) DEFAULT 0,
  `status` varchar(20) DEFAULT 'accepted',
  `removed_reason` text DEFAULT NULL,
  `removed_at` datetime DEFAULT NULL,
  `removed_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bids`
--

INSERT INTO `bids` (`bid_id`, `auction_id`, `bidder_id`, `bid_amount`, `bid_time`, `is_auto_bid`, `status`, `removed_reason`, `removed_at`, `removed_by`) VALUES
(1, 1, 3, 1550.00, '2026-08-07 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(2, 1, 6, 1650.00, '2026-08-08 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(3, 1, 8, 1750.00, '2026-08-09 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(4, 2, 7, 320.00, '2026-08-08 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(5, 2, 3, 340.00, '2026-08-09 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(6, 3, 8, 1250.00, '2026-08-06 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(7, 3, 6, 1350.00, '2026-08-07 10:54:32', 0, 'accepted', NULL, NULL, NULL),
(26, 2, 9, 360.00, '2026-08-09 12:18:49', 0, 'accepted', NULL, NULL, NULL),
(27, 9, 10, 24445.00, '2026-08-09 13:07:11', 0, 'accepted', NULL, NULL, NULL),
(28, 2, 10, 460.00, '2026-08-09 13:11:05', 0, 'accepted', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `payments`
--

CREATE TABLE `payments` (
  `payment_id` int(11) NOT NULL,
  `auction_id` int(11) NOT NULL,
  `buyer_id` int(11) NOT NULL,
  `seller_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(50) DEFAULT 'credit_card',
  `shipping_address` text DEFAULT NULL,
  `payment_status` varchar(20) DEFAULT 'pending',
  `payment_date` datetime DEFAULT NULL,
  `transaction_id` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `payments`
--

INSERT INTO `payments` (`payment_id`, `auction_id`, `buyer_id`, `seller_id`, `amount`, `payment_method`, `shipping_address`, `payment_status`, `payment_date`, `transaction_id`, `created_at`) VALUES
(1, 4, 3, 4, 720.00, 'bank_transfer', '12 Samora Machel Ave, Harare, Zimbabwe', 'completed', '2026-08-09 14:51:44', 'ADM1786279904276', '2026-08-09 10:54:32'),
(2, 6, 6, 5, 1100.00, 'credit_card', '45 Borrowdale Rd, Harare, Zimbabwe', 'completed', '2026-08-07 12:54:32', 'TXN-NECKLACE-0002', '2026-08-09 10:54:32');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `user_type` varchar(20) DEFAULT 'buyer',
  `profile_image` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `email`, `password`, `first_name`, `last_name`, `phone`, `user_type`, `profile_image`, `created_at`) VALUES
(1, 'admin', 'admin@auction.com', 'scrypt:32768:8:1$9S2L3kEGuiFAfjgQ$e2d14cc60165bd3d57e2975f1fba2ff6000403183197191cbdbd5c157c5a463f5ad33dd5b0ed7d7dbf5ddf200d0972bcc7c303570ec3493b5bf0ea7ca858fc88', 'System', 'Admin', '', 'admin', 'avatar_1_1786280178.jpg', '2026-08-09 10:36:17'),
(2, 'john', 'john@email.com', 'scrypt:32768:8:1$9S2L3kEGuiFAfjgQ$e2d14cc60165bd3d57e2975f1fba2ff6000403183197191cbdbd5c157c5a463f5ad33dd5b0ed7d7dbf5ddf200d0972bcc7c303570ec3493b5bf0ea7ca858fc88', 'John', 'Seller', '', 'seller', NULL, '2026-08-09 10:36:17'),
(3, 'jane', 'jane@email.com', 'scrypt:32768:8:1$9S2L3kEGuiFAfjgQ$e2d14cc60165bd3d57e2975f1fba2ff6000403183197191cbdbd5c157c5a463f5ad33dd5b0ed7d7dbf5ddf200d0972bcc7c303570ec3493b5bf0ea7ca858fc88', 'Jane', 'Buyer', '', 'buyer', NULL, '2026-08-09 10:36:17'),
(4, 'mike', 'mike@email.com', 'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8', 'Mike', 'Turner', '0771111111', 'seller', NULL, '2026-08-09 10:54:32'),
(5, 'sarah', 'sarah@email.com', 'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8', 'Sarah', 'Lopez', '0772222222', 'seller', NULL, '2026-08-09 10:54:32'),
(6, 'alex', 'alex@email.com', 'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8', 'Alex', 'Nguyen', '0773333333', 'buyer', NULL, '2026-08-09 10:54:32'),
(7, 'emma', 'emma@email.com', 'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8', 'Emma', 'Chikara', '0774444444', 'buyer', NULL, '2026-08-09 10:54:32'),
(8, 'chris', 'chris@email.com', 'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8', 'Chris', 'Moyo', '0775555555', 'buyer', NULL, '2026-08-09 10:54:32'),
(9, 'mmeplodge@gmail.com', 'mmeplodge@gmail.com', 'scrypt:32768:8:1$qrwpaJ7tXagHt054$8484dad4ba636169dadc717fe2a5e7281b9489f41306edf78eb77dbe2ddcee98e14a21447c3bc0a741c0870ce2c009e3b88509a6ed688e56e54260babc5b007a', 'Meplodge', 'Moyana', '0784882154', 'buyer', NULL, '2026-08-09 12:17:55'),
(10, 'john@email.com', 'shashi@gmail.com', 'scrypt:32768:8:1$IWwX8ADhMgMTY8hK$3d1f1fbec550737c3594ecaa6f9a45ecd9a37e94d8dabbf4e42f5d28f7a527abb7992fd431aef9f4e0137a6b7b19076f6580a47b9aa3d557e7591863883e0361', 'shashi', 'chimuti', '0784882154', 'buyer', 'avatar_10_1786280954.jpg', '2026-08-09 13:05:23');

-- --------------------------------------------------------

--
-- Table structure for table `watchlist`
--

CREATE TABLE `watchlist` (
  `watchlist_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `auction_id` int(11) NOT NULL,
  `added_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `watchlist`
--

INSERT INTO `watchlist` (`watchlist_id`, `user_id`, `auction_id`, `added_at`) VALUES
(1, 3, 3, '2026-08-09 10:54:32'),
(2, 6, 1, '2026-08-09 10:54:32'),
(3, 7, 5, '2026-08-09 10:54:32'),
(4, 8, 8, '2026-08-09 10:54:32'),
(5, 9, 1, '2026-08-09 12:18:18');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `auctions`
--
ALTER TABLE `auctions`
  ADD PRIMARY KEY (`auction_id`),
  ADD KEY `fk_auctions_seller` (`seller_id`),
  ADD KEY `fk_auctions_winner` (`winner_id`);

--
-- Indexes for table `auction_images`
--
ALTER TABLE `auction_images`
  ADD PRIMARY KEY (`image_id`),
  ADD KEY `fk_images_auction` (`auction_id`);

--
-- Indexes for table `bids`
--
ALTER TABLE `bids`
  ADD PRIMARY KEY (`bid_id`),
  ADD KEY `fk_bids_auction` (`auction_id`),
  ADD KEY `fk_bids_bidder` (`bidder_id`);

--
-- Indexes for table `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`payment_id`),
  ADD KEY `fk_payments_auction` (`auction_id`),
  ADD KEY `fk_payments_buyer` (`buyer_id`),
  ADD KEY `fk_payments_seller` (`seller_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `watchlist`
--
ALTER TABLE `watchlist`
  ADD PRIMARY KEY (`watchlist_id`),
  ADD KEY `fk_watchlist_user` (`user_id`),
  ADD KEY `fk_watchlist_auction` (`auction_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `auctions`
--
ALTER TABLE `auctions`
  MODIFY `auction_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `auction_images`
--
ALTER TABLE `auction_images`
  MODIFY `image_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `bids`
--
ALTER TABLE `bids`
  MODIFY `bid_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT for table `payments`
--
ALTER TABLE `payments`
  MODIFY `payment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `watchlist`
--
ALTER TABLE `watchlist`
  MODIFY `watchlist_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `auctions`
--
ALTER TABLE `auctions`
  ADD CONSTRAINT `fk_auctions_seller` FOREIGN KEY (`seller_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_auctions_winner` FOREIGN KEY (`winner_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `auction_images`
--
ALTER TABLE `auction_images`
  ADD CONSTRAINT `fk_images_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions` (`auction_id`) ON DELETE CASCADE;

--
-- Constraints for table `bids`
--
ALTER TABLE `bids`
  ADD CONSTRAINT `fk_bids_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions` (`auction_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_bids_bidder` FOREIGN KEY (`bidder_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `fk_payments_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions` (`auction_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_payments_buyer` FOREIGN KEY (`buyer_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_payments_seller` FOREIGN KEY (`seller_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `watchlist`
--
ALTER TABLE `watchlist`
  ADD CONSTRAINT `fk_watchlist_auction` FOREIGN KEY (`auction_id`) REFERENCES `auctions` (`auction_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_watchlist_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
