import MySQLdb
from werkzeug.security import generate_password_hash


def _get_connection(app, use_database=True):
    config = {
        "host": app.config.get("MYSQL_HOST", "localhost"),
        "user": app.config.get("MYSQL_USER", "root"),
        "passwd": app.config.get("MYSQL_PASSWORD", "") or "",
        "port": app.config.get("MYSQL_PORT", 3306),
        "charset": "utf8mb4",
    }

    if use_database:
        config["db"] = app.config.get("MYSQL_DB", "auction_db")

    return MySQLdb.connect(**config)


def create_database_if_not_exists(app):
    db_name = app.config.get("MYSQL_DB", "auction_db")
    conn = _get_connection(app, use_database=False)
    cur = conn.cursor()

    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    conn.commit()

    cur.close()
    conn.close()


def create_default_admin(app):
    admin_username = app.config.get("ADMIN_USERNAME", "admin")
    admin_email = app.config.get("ADMIN_EMAIL", "admin@auction.com")
    admin_password = app.config.get("ADMIN_PASSWORD", "password123")

    conn = _get_connection(app, use_database=True)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE email = %s OR username = %s LIMIT 1",
        (admin_email, admin_username)
    )
    existing = cur.fetchone()

    if not existing:
        hashed_password = generate_password_hash(admin_password)
        cur.execute("""
            INSERT INTO users (username, email, password, first_name, last_name, phone, user_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            admin_username,
            admin_email,
            hashed_password,
            "System",
            "Admin",
            "",
            "admin"
        ))

    conn.commit()
    cur.close()
    conn.close()


def add_column_if_missing(cur, table, column, definition):
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s
    """, (table, column))

    if cur.fetchone()[0] == 0:
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
        print(f"Added column {table}.{column}")


def initialize_database(app):
    create_database_if_not_exists(app)

    conn = _get_connection(app, use_database=True)
    cur = conn.cursor()

    create_statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            phone VARCHAR(20),
            user_type VARCHAR(20) DEFAULT 'buyer',
            profile_image VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auctions (
            auction_id INT AUTO_INCREMENT PRIMARY KEY,
            seller_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            starting_price DECIMAL(10,2) NOT NULL,
            current_price DECIMAL(10,2) NOT NULL,
            min_bid_increment DECIMAL(10,2) DEFAULT 1.00,
            start_date DATETIME,
            end_date DATETIME,
            status VARCHAR(20) DEFAULT 'draft',
            total_bids INT DEFAULT 0,
            winner_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS auction_images (
            image_id INT AUTO_INCREMENT PRIMARY KEY,
            auction_id INT NOT NULL,
            image_url VARCHAR(255) NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS bids (
            bid_id INT AUTO_INCREMENT PRIMARY KEY,
            auction_id INT NOT NULL,
            bidder_id INT NOT NULL,
            bid_amount DECIMAL(10,2) NOT NULL,
            bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_auto_bid BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'accepted',
            removed_reason TEXT,
            removed_at DATETIME,
            removed_by INT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            auction_id INT NOT NULL,
            buyer_id INT NOT NULL,
            seller_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_method VARCHAR(50) DEFAULT 'credit_card',
            shipping_address TEXT,
            payment_status VARCHAR(20) DEFAULT 'pending',
            payment_date DATETIME,
            transaction_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            watchlist_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            auction_id INT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS admin_actions (
            action_id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id INT NOT NULL,
            action VARCHAR(50) NOT NULL,
            target_type VARCHAR(30) NOT NULL,
            target_id INT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_actions_target (target_type, target_id),
            INDEX idx_actions_created (created_at)
        )
        """
    ]

    for statement in create_statements:
        cur.execute(statement)

    # Migrations for databases created before bid moderation existed
    for column, definition in [
        ("status", "VARCHAR(20) DEFAULT 'accepted'"),
        ("removed_reason", "TEXT"),
        ("removed_at", "DATETIME"),
        ("removed_by", "INT"),
    ]:
        add_column_if_missing(cur, "bids", column, definition)

    # Migration: add suspension flag to users for admin user management
    add_column_if_missing(cur, "users", "is_suspended", "TINYINT(1) DEFAULT 0")

    cur.execute("UPDATE bids SET status = 'accepted' WHERE status IS NULL")

    conn.commit()
    cur.close()
    conn.close()

    create_default_admin(app)

    print("Database tables initialized successfully.")
    print("Default admin account ensured.")