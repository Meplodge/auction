-- ============================================================
-- Mock / Seed Data for Auction System (auction_db)
--
-- Adds extra demo users, auctions, bids, watchlist entries and
-- payments so the app has realistic data to browse/test with.
--
-- Run AFTER auction_db.sql (or after app.py has created the
-- schema) so the tables already exist. All demo user passwords
-- are: password123
--
-- Usage:
--   C:\xampp\mysql\bin\mysql.exe -u root auction_db < mock_data.sql
-- Or via phpMyAdmin: select auction_db -> Import -> mock_data.sql
-- ============================================================

USE `auction_db`;

-- ------------------------------------------------------------
-- Extra demo users (password123 for all)
-- ------------------------------------------------------------
INSERT INTO `users` (`username`, `email`, `password`, `first_name`, `last_name`, `phone`, `user_type`)
VALUES
    ('mike', 'mike@email.com',
     'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8',
     'Mike', 'Turner', '0771111111', 'seller'),
    ('sarah', 'sarah@email.com',
     'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8',
     'Sarah', 'Lopez', '0772222222', 'seller'),
    ('alex', 'alex@email.com',
     'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8',
     'Alex', 'Nguyen', '0773333333', 'buyer'),
    ('emma', 'emma@email.com',
     'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8',
     'Emma', 'Chikara', '0774444444', 'buyer'),
    ('chris', 'chris@email.com',
     'scrypt:32768:8:1$Cv3vU6laVc1IG2n6$818c92c691c1f7a6a1224780c52a6526c3329dd2fcca9911f14237c7030d280fe007d557382e593d8d1cf9e0597dcfdf5356eb36769a8bd8c3aac7d5251f6fc8',
     'Chris', 'Moyo', '0775555555', 'buyer');

-- ------------------------------------------------------------
-- Auctions
-- Seller ids are looked up by username so this works no matter
-- what auto-increment ids already exist in the table.
-- ------------------------------------------------------------
INSERT INTO `auctions`
    (`seller_id`, `title`, `description`, `category`, `starting_price`, `current_price`,
     `min_bid_increment`, `start_date`, `end_date`, `status`, `total_bids`, `winner_id`)
VALUES
    ((SELECT user_id FROM users WHERE username='john'),
     'Vintage Rolex Submariner Watch',
     'Genuine 1978 Rolex Submariner, recently serviced, comes with original box and papers.',
     'Watches', 1500.00, 1750.00, 50.00,
     DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_ADD(NOW(), INTERVAL 5 DAY), 'active', 3, NULL),

    ((SELECT user_id FROM users WHERE username='john'),
     'Antique Oak Writing Desk',
     'Solid oak roll-top desk from the early 1900s, fully restored with working lock.',
     'Furniture', 300.00, 340.00, 20.00,
     DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 6 DAY), 'active', 2, NULL),

    ((SELECT user_id FROM users WHERE username='mike'),
     'Gaming Laptop - RTX 4080, 32GB RAM',
     'High-end gaming laptop, barely used, includes charger and original packaging.',
     'Electronics', 1200.00, 1450.00, 25.00,
     DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_ADD(NOW(), INTERVAL 4 DAY), 'active', 4, NULL),

    ((SELECT user_id FROM users WHERE username='mike'),
     'Rare Silver Age Comic Book Collection',
     'Set of 12 Silver Age comics in protective sleeves, great condition for their age.',
     'Collectibles', 500.00, 720.00, 20.00,
     DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY), 'closed', 5,
     (SELECT user_id FROM users WHERE username='jane')),

    ((SELECT user_id FROM users WHERE username='sarah'),
     'Trek X-Caliber Mountain Bike',
     'Aluminum frame mountain bike, size L, lightly used, well maintained.',
     'Sports', 250.00, 300.00, 15.00,
     DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 3 DAY), 'active', 2, NULL),

    ((SELECT user_id FROM users WHERE username='sarah'),
     'Diamond Pendant Necklace, 18k Gold',
     '1 carat diamond pendant on an 18k gold chain, includes certificate of authenticity.',
     'Jewelry', 800.00, 1100.00, 50.00,
     DATE_SUB(NOW(), INTERVAL 8 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), 'closed', 4,
     (SELECT user_id FROM users WHERE username='alex')),

    ((SELECT user_id FROM users WHERE username='john'),
     'Fender Stratocaster Electric Guitar',
     'Classic Fender Stratocaster in sunburst finish, includes hard case.',
     'Musical Instruments', 600.00, 600.00, 25.00,
     NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), 'draft', 0, NULL),

    ((SELECT user_id FROM users WHERE username='mike'),
     'Original Oil Painting - Countryside Landscape',
     'Hand-painted oil on canvas, 60x80cm, framed and ready to hang.',
     'Art', 150.00, 190.00, 10.00,
     DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_ADD(NOW(), INTERVAL 2 DAY), 'active', 3, NULL);

-- ------------------------------------------------------------
-- Bids
-- ------------------------------------------------------------
INSERT INTO `bids` (`auction_id`, `bidder_id`, `bid_amount`, `bid_time`, `is_auto_bid`)
VALUES
    -- Rolex watch
    ((SELECT auction_id FROM auctions WHERE title='Vintage Rolex Submariner Watch'),
     (SELECT user_id FROM users WHERE username='jane'), 1550.00, DATE_SUB(NOW(), INTERVAL 2 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Vintage Rolex Submariner Watch'),
     (SELECT user_id FROM users WHERE username='alex'), 1650.00, DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Vintage Rolex Submariner Watch'),
     (SELECT user_id FROM users WHERE username='chris'), 1750.00, NOW(), FALSE),

    -- Antique desk
    ((SELECT auction_id FROM auctions WHERE title='Antique Oak Writing Desk'),
     (SELECT user_id FROM users WHERE username='emma'), 320.00, DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Antique Oak Writing Desk'),
     (SELECT user_id FROM users WHERE username='jane'), 340.00, NOW(), FALSE),

    -- Gaming laptop
    ((SELECT auction_id FROM auctions WHERE title='Gaming Laptop - RTX 4080, 32GB RAM'),
     (SELECT user_id FROM users WHERE username='chris'), 1250.00, DATE_SUB(NOW(), INTERVAL 3 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Gaming Laptop - RTX 4080, 32GB RAM'),
     (SELECT user_id FROM users WHERE username='alex'), 1350.00, DATE_SUB(NOW(), INTERVAL 2 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Gaming Laptop - RTX 4080, 32GB RAM'),
     (SELECT user_id FROM users WHERE username='emma'), 1400.00, DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Gaming Laptop - RTX 4080, 32GB RAM'),
     (SELECT user_id FROM users WHERE username='jane'), 1450.00, NOW(), FALSE),

    -- Comic book collection (closed, winner jane)
    ((SELECT auction_id FROM auctions WHERE title='Rare Silver Age Comic Book Collection'),
     (SELECT user_id FROM users WHERE username='alex'), 550.00, DATE_SUB(NOW(), INTERVAL 9 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Rare Silver Age Comic Book Collection'),
     (SELECT user_id FROM users WHERE username='chris'), 600.00, DATE_SUB(NOW(), INTERVAL 7 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Rare Silver Age Comic Book Collection'),
     (SELECT user_id FROM users WHERE username='emma'), 650.00, DATE_SUB(NOW(), INTERVAL 5 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Rare Silver Age Comic Book Collection'),
     (SELECT user_id FROM users WHERE username='alex'), 690.00, DATE_SUB(NOW(), INTERVAL 3 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Rare Silver Age Comic Book Collection'),
     (SELECT user_id FROM users WHERE username='jane'), 720.00, DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE),

    -- Mountain bike
    ((SELECT auction_id FROM auctions WHERE title='Trek X-Caliber Mountain Bike'),
     (SELECT user_id FROM users WHERE username='chris'), 275.00, DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Trek X-Caliber Mountain Bike'),
     (SELECT user_id FROM users WHERE username='emma'), 300.00, NOW(), FALSE),

    -- Diamond necklace (closed, winner alex)
    ((SELECT auction_id FROM auctions WHERE title='Diamond Pendant Necklace, 18k Gold'),
     (SELECT user_id FROM users WHERE username='jane'), 900.00, DATE_SUB(NOW(), INTERVAL 7 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Diamond Pendant Necklace, 18k Gold'),
     (SELECT user_id FROM users WHERE username='emma'), 1000.00, DATE_SUB(NOW(), INTERVAL 5 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Diamond Pendant Necklace, 18k Gold'),
     (SELECT user_id FROM users WHERE username='chris'), 1050.00, DATE_SUB(NOW(), INTERVAL 4 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Diamond Pendant Necklace, 18k Gold'),
     (SELECT user_id FROM users WHERE username='alex'), 1100.00, DATE_SUB(NOW(), INTERVAL 2 DAY), FALSE),

    -- Oil painting
    ((SELECT auction_id FROM auctions WHERE title='Original Oil Painting - Countryside Landscape'),
     (SELECT user_id FROM users WHERE username='jane'), 160.00, DATE_SUB(NOW(), INTERVAL 4 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Original Oil Painting - Countryside Landscape'),
     (SELECT user_id FROM users WHERE username='alex'), 175.00, DATE_SUB(NOW(), INTERVAL 2 DAY), FALSE),
    ((SELECT auction_id FROM auctions WHERE title='Original Oil Painting - Countryside Landscape'),
     (SELECT user_id FROM users WHERE username='chris'), 190.00, DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE);

-- ------------------------------------------------------------
-- Watchlist entries
-- ------------------------------------------------------------
INSERT INTO `watchlist` (`user_id`, `auction_id`, `added_at`)
VALUES
    ((SELECT user_id FROM users WHERE username='jane'),
     (SELECT auction_id FROM auctions WHERE title='Gaming Laptop - RTX 4080, 32GB RAM'), NOW()),
    ((SELECT user_id FROM users WHERE username='alex'),
     (SELECT auction_id FROM auctions WHERE title='Vintage Rolex Submariner Watch'), NOW()),
    ((SELECT user_id FROM users WHERE username='emma'),
     (SELECT auction_id FROM auctions WHERE title='Trek X-Caliber Mountain Bike'), NOW()),
    ((SELECT user_id FROM users WHERE username='chris'),
     (SELECT auction_id FROM auctions WHERE title='Original Oil Painting - Countryside Landscape'), NOW());

-- ------------------------------------------------------------
-- Payments (for closed / won auctions)
-- ------------------------------------------------------------
INSERT INTO `payments`
    (`auction_id`, `buyer_id`, `seller_id`, `amount`, `payment_method`,
     `shipping_address`, `payment_status`, `payment_date`, `transaction_id`)
VALUES
    ((SELECT auction_id FROM auctions WHERE title='Rare Silver Age Comic Book Collection'),
     (SELECT user_id FROM users WHERE username='jane'),
     (SELECT user_id FROM users WHERE username='mike'),
     720.00, 'credit_card', '12 Samora Machel Ave, Harare, Zimbabwe',
     'completed', DATE_SUB(NOW(), INTERVAL 1 DAY), 'TXN-COMIC-0001'),

    ((SELECT auction_id FROM auctions WHERE title='Diamond Pendant Necklace, 18k Gold'),
     (SELECT user_id FROM users WHERE username='alex'),
     (SELECT user_id FROM users WHERE username='sarah'),
     1100.00, 'credit_card', '45 Borrowdale Rd, Harare, Zimbabwe',
     'completed', DATE_SUB(NOW(), INTERVAL 2 DAY), 'TXN-NECKLACE-0002');
