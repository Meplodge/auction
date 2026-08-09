from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import sys
import json
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from database_ops import initialize_database

# ============================================
# APP CONFIGURATION
# ============================================
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'auction_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# File Upload Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Extensions
mysql = MySQL(app)
initialize_database(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# ============================================
# USER CLASS
# ============================================
class User(UserMixin):
    def __init__(self, user_id, username, email, first_name, last_name, user_type, phone=None, profile_image=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.user_type = user_type
        self.phone = phone
        self.profile_image = profile_image
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        
        if user:
            return User(
                user_id=user['user_id'],
                username=user['username'],
                email=user['email'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                user_type=user['user_type'],
                phone=user.get('phone'),
                profile_image=user.get('profile_image')
            )
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# ============================================
# HELPER FUNCTIONS
# ============================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_dashboard_redirect(user_or_role):
    if hasattr(user_or_role, 'user_type'):
        role = user_or_role.user_type
    elif isinstance(user_or_role, dict):
        role = user_or_role.get('user_type', 'buyer')
    else:
        role = str(user_or_role or 'buyer')

    role = (role or 'buyer').strip().lower()

    if role == 'admin':
        return url_for('admin_dashboard')
    elif role == 'seller':
        return url_for('seller_dashboard')
    else:
        return url_for('buyer_dashboard')

def update_auction_status():
    """Close expired auctions, award them to the highest bidder and raise an invoice."""
    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT auction_id, seller_id, current_price
            FROM auctions
            WHERE end_date < NOW() AND status = 'active'
        """)
        expiring = cur.fetchall()

        for auction in expiring:
            cur.execute("""
                SELECT bidder_id, bid_amount
                FROM bids
                WHERE auction_id = %s AND status = 'accepted'
                ORDER BY bid_amount DESC, bid_time ASC
                LIMIT 1
            """, (auction['auction_id'],))
            top = cur.fetchone()

            cur.execute("""
                UPDATE auctions
                SET status = 'closed', winner_id = %s
                WHERE auction_id = %s
            """, (top['bidder_id'] if top else None, auction['auction_id']))

            if top:
                create_invoice(cur, auction['auction_id'], top['bidder_id'],
                               auction['seller_id'], top['bid_amount'])

        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print(f"Error updating auction status: {e}")

def recalculate_auction(cur, auction_id):
    """Recompute price, bid count and winner from the accepted bids only.

    Called after an admin removes a bid so the lot reflects reality again.
    """
    cur.execute("""
        SELECT COUNT(*) as bid_count, MAX(bid_amount) as top_amount
        FROM bids
        WHERE auction_id = %s AND status = 'accepted'
    """, (auction_id,))
    summary = cur.fetchone()

    cur.execute("SELECT starting_price, status FROM auctions WHERE auction_id = %s", (auction_id,))
    auction = cur.fetchone()
    if not auction:
        return

    price = summary['top_amount'] if summary['top_amount'] is not None else auction['starting_price']

    winner_id = None
    if auction['status'] == 'closed' and summary['bid_count']:
        cur.execute("""
            SELECT bidder_id FROM bids
            WHERE auction_id = %s AND status = 'accepted'
            ORDER BY bid_amount DESC, bid_time ASC
            LIMIT 1
        """, (auction_id,))
        top = cur.fetchone()
        winner_id = top['bidder_id'] if top else None

    cur.execute("""
        UPDATE auctions
        SET current_price = %s, total_bids = %s, winner_id = %s
        WHERE auction_id = %s
    """, (price, summary['bid_count'] or 0, winner_id, auction_id))

def create_invoice(cur, auction_id, buyer_id, seller_id, amount):
    """Insert a pending payment for a won lot unless one already exists."""
    cur.execute("SELECT payment_id FROM payments WHERE auction_id = %s", (auction_id,))
    if cur.fetchone():
        return False

    cur.execute("""
        INSERT INTO payments (auction_id, buyer_id, seller_id, amount, payment_status)
        VALUES (%s, %s, %s, %s, 'pending')
    """, (auction_id, buyer_id, seller_id, amount))
    return True

def daily_series(sql, params=(), days=14):
    """Return {labels, values} for the last `days` days, zero-filled.

    `sql` must select a `day` (DATE) column and a `total` column.
    """
    today = datetime.now().date()
    span = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    buckets = {d: 0 for d in span}

    try:
        cur = mysql.connection.cursor()
        cur.execute(sql, params)
        for row in cur.fetchall():
            day = row['day']
            if hasattr(day, 'date'):
                day = day.date()
            if day in buckets:
                buckets[day] = float(row['total'] or 0)
        cur.close()
    except Exception as e:
        print(f"Error building daily series: {e}")

    return {
        'labels': [d.strftime('%d %b') for d in span],
        'values': [buckets[d] for d in span]
    }

def get_categories():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT DISTINCT category 
            FROM auctions 
            WHERE category IS NOT NULL 
            ORDER BY category
        """)
        categories = cur.fetchall()
        cur.close()
        return [c['category'] for c in categories]
    except:
        return ['Electronics', 'Furniture', 'Cars', 'Fashion', 'Luxury', 'Books']

def get_auction_statistics():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) as total FROM auctions")
        total_auctions = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM auctions WHERE status = 'active'")
        active_auctions = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM auctions WHERE status = 'closed'")
        closed_auctions = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM users")
        total_users = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM bids WHERE status = 'accepted'")
        total_bids = cur.fetchone()['total']
        
        cur.execute("SELECT SUM(amount) as total FROM payments WHERE payment_status = 'completed'")
        total_revenue = cur.fetchone()['total'] or 0
        
        cur.close()
        return {
            'total_auctions': total_auctions,
            'active_auctions': active_auctions,
            'closed_auctions': closed_auctions,
            'total_users': total_users,
            'total_bids': total_bids,
            'total_revenue': total_revenue
        }
    except:
        return {
            'total_auctions': 0,
            'active_auctions': 0,
            'closed_auctions': 0,
            'total_users': 0,
            'total_bids': 0,
            'total_revenue': 0
        }

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    update_auction_status()
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT a.*, u.username, u.first_name, u.last_name,
                   (SELECT COUNT(*) FROM auction_images WHERE auction_id = a.auction_id) as image_count,
                   (SELECT image_url FROM auction_images WHERE auction_id = a.auction_id AND is_primary = TRUE LIMIT 1) as primary_image
            FROM auctions a
            LEFT JOIN users u ON a.seller_id = u.user_id
            WHERE a.status = 'active' OR a.status = 'closed'
            ORDER BY a.created_at DESC
            LIMIT 12
        """)
        auctions = cur.fetchall()
        cur.close()
        return render_template('index.html', auctions=auctions, categories=get_categories())
    except Exception as e:
        print(f"Index error: {e}")
        flash('Error loading auctions. Please try again.', 'danger')
        return render_template('index.html', auctions=[], categories=[])

@app.route('/fixed')
def fixed():
    """Non-scrolling fixed landing page."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) as live FROM auctions WHERE status = 'active'")
        live_count = cur.fetchone()['live']
        cur.close()
    except Exception:
        live_count = 0
    return render_template('fixed_landing.html', live_count=live_count)

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', 'buyer')
        
        if not all([username, email, password, first_name, last_name]):
            flash('Please fill all required fields', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return render_template('register.html')
        
        try:
            cur = mysql.connection.cursor()
            
            # Check username
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                flash('Username already taken', 'danger')
                cur.close()
                return render_template('register.html')
            
            # Check email
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash('Email already registered', 'danger')
                cur.close()
                return render_template('register.html')
            
            hashed_password = generate_password_hash(password)
            
            cur.execute("""
                INSERT INTO users (username, email, password, first_name, last_name, phone, user_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, email, hashed_password, first_name, last_name, phone, user_type))
            mysql.connection.commit()
            cur.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()

            if user and check_password_hash(user['password'], password):
                user_obj = User(
                    user_id=user['user_id'],
                    username=user['username'],
                    email=user['email'],
                    first_name=user['first_name'],
                    last_name=user['last_name'],
                    user_type=user['user_type'],
                    phone=user.get('phone'),
                    profile_image=user.get('profile_image')
                )
                login_user(user_obj, remember=remember)
                flash(f'Welcome back, {user["first_name"]}!', 'success')

                return redirect(get_dashboard_redirect(user_obj))
            else:
                flash('Invalid email or password', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# ============================================
# DASHBOARDS
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(get_dashboard_redirect(current_user))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    stats = get_auction_statistics()
    
    try:
        cur = mysql.connection.cursor()
        
        # Recent activity: every bid, including any an admin has removed
        cur.execute("""
            SELECT b.*, u.username, u.first_name, u.last_name,
                   a.title as auction_title, a.status as auction_status
            FROM bids b
            JOIN users u ON b.bidder_id = u.user_id
            JOIN auctions a ON b.auction_id = a.auction_id
            ORDER BY b.bid_time DESC
            LIMIT 40
        """)
        recent_bids = cur.fetchall()
        
        # Recent users
        cur.execute("""
            SELECT * FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_users = cur.fetchall()

        # Every bidder, with their activity, for admin oversight
        cur.execute("""
            SELECT u.user_id, u.username, u.first_name, u.last_name, u.email,
                   u.user_type, u.created_at,
                   (SELECT COUNT(*) FROM bids
                     WHERE bidder_id = u.user_id AND status = 'accepted') as bid_count,
                   (SELECT MAX(bid_amount) FROM bids
                     WHERE bidder_id = u.user_id AND status = 'accepted') as highest_bid,
                   (SELECT COUNT(*) FROM bids
                     WHERE bidder_id = u.user_id AND status = 'removed') as removed_bids,
                   (SELECT COUNT(*) FROM auctions WHERE winner_id = u.user_id) as wins,
                   (SELECT COUNT(*) FROM payments
                     WHERE buyer_id = u.user_id AND payment_status = 'pending') as outstanding
            FROM users u
            WHERE u.user_type = 'buyer'
            ORDER BY bid_count DESC, u.created_at DESC
        """)
        bidders = cur.fetchall()

        # All payments across the platform
        cur.execute("""
            SELECT p.*, a.title as auction_title,
                   b.first_name as buyer_first_name, b.last_name as buyer_last_name,
                   s.first_name as seller_first_name, s.last_name as seller_last_name
            FROM payments p
            JOIN auctions a ON p.auction_id = a.auction_id
            JOIN users b ON p.buyer_id = b.user_id
            JOIN users s ON p.seller_id = s.user_id
            ORDER BY p.payment_status = 'completed', p.created_at DESC
            LIMIT 25
        """)
        all_payments = cur.fetchall()

        # Closed lots with a winner but no invoice yet
        cur.execute("""
            SELECT a.auction_id, a.title, a.current_price, a.end_date,
                   a.winner_id, a.seller_id,
                   w.first_name as winner_first_name, w.last_name as winner_last_name
            FROM auctions a
            JOIN users w ON a.winner_id = w.user_id
            LEFT JOIN payments p ON p.auction_id = a.auction_id
            WHERE a.status = 'closed' AND a.winner_id IS NOT NULL AND p.payment_id IS NULL
            ORDER BY a.end_date DESC
        """)
        uninvoiced = cur.fetchall()

        cur.close()

        bids_series = daily_series("""
            SELECT DATE(bid_time) as day, COUNT(*) as total
            FROM bids
            WHERE status = 'accepted'
              AND bid_time >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            GROUP BY DATE(bid_time)
        """)

        revenue_series = daily_series("""
            SELECT DATE(payment_date) as day, SUM(amount) as total
            FROM payments
            WHERE payment_status = 'completed'
              AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            GROUP BY DATE(payment_date)
        """)

        return render_template('admin_dashboard.html', 
                              stats=stats, 
                              recent_bids=recent_bids,
                              recent_users=recent_users,
                              bidders=bidders,
                              all_payments=all_payments,
                              uninvoiced=uninvoiced,
                              bids_series=bids_series,
                              revenue_series=revenue_series)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard', 'danger')
        return redirect(url_for('index'))

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if current_user.user_type not in ['seller', 'admin']:
        flash('Access denied. Seller only.', 'danger')
        return redirect(url_for('index'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT a.*,
                   (SELECT COUNT(*) FROM bids
                     WHERE auction_id = a.auction_id AND status = 'accepted') as bid_count,
                   (SELECT COUNT(*) FROM auction_images WHERE auction_id = a.auction_id) as image_count
            FROM auctions a
            WHERE a.seller_id = %s
            ORDER BY a.created_at DESC
        """, (current_user.id,))
        auctions = cur.fetchall()
        
        # Stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_auctions,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_auctions,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_auctions,
                (SELECT COUNT(*) FROM bids
                  WHERE status = 'accepted'
                    AND auction_id IN (SELECT auction_id FROM auctions WHERE seller_id = %s)) as total_bids
            FROM auctions
            WHERE seller_id = %s
        """, (current_user.id, current_user.id))
        stats = cur.fetchone()
        cur.close()

        bids_series = daily_series("""
            SELECT DATE(b.bid_time) as day, COUNT(*) as total
            FROM bids b
            JOIN auctions a ON b.auction_id = a.auction_id
            WHERE a.seller_id = %s AND b.status = 'accepted'
              AND b.bid_time >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            GROUP BY DATE(b.bid_time)
        """, (current_user.id,))

        earnings_series = daily_series("""
            SELECT DATE(payment_date) as day, SUM(amount) as total
            FROM payments
            WHERE seller_id = %s AND payment_status = 'completed'
              AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            GROUP BY DATE(payment_date)
        """, (current_user.id,))

        return render_template('seller_dashboard.html', auctions=auctions, stats=stats,
                              bids_series=bids_series, earnings_series=earnings_series)
    except Exception as e:
        print(f"Seller dashboard error: {e}")
        flash('Error loading seller dashboard', 'danger')
        return redirect(url_for('index'))

@app.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    if current_user.user_type not in ['buyer', 'admin']:
        flash('Access denied. Buyer only.', 'danger')
        return redirect(url_for('index'))

    try:
        cur = mysql.connection.cursor()

        # My bids (removed bids stay visible so the reason can be shown)
        cur.execute("""
            SELECT b.*, a.title, a.status as auction_status, a.end_date,
                   (SELECT MAX(bid_amount) FROM bids
                     WHERE auction_id = b.auction_id AND status = 'accepted') as highest_bid
            FROM bids b
            JOIN auctions a ON b.auction_id = a.auction_id
            WHERE b.bidder_id = %s
            ORDER BY b.bid_time DESC
            LIMIT 20
        """, (current_user.id,))
        my_bids = cur.fetchall()
        
        # My watchlist
        cur.execute("""
            SELECT w.*, a.title, a.current_price, a.end_date, a.status as auction_status,
                   (SELECT image_url FROM auction_images WHERE auction_id = a.auction_id AND is_primary = TRUE LIMIT 1) as primary_image
            FROM watchlist w
            JOIN auctions a ON w.auction_id = a.auction_id
            WHERE w.user_id = %s
            ORDER BY w.added_at DESC
        """, (current_user.id,))
        watchlist = cur.fetchall()
        
        # My wins
        cur.execute("""
            SELECT a.*, u.username as seller_username, u.first_name as seller_first_name, u.last_name as seller_last_name
            FROM auctions a
            JOIN users u ON a.seller_id = u.user_id
            WHERE a.winner_id = %s AND a.status = 'closed'
            ORDER BY a.end_date DESC
        """, (current_user.id,))
        wins = cur.fetchall()
        
        cur.close()

        bids_series = daily_series("""
            SELECT DATE(bid_time) as day, COUNT(*) as total
            FROM bids
            WHERE bidder_id = %s AND status = 'accepted'
              AND bid_time >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            GROUP BY DATE(bid_time)
        """, (current_user.id,))

        spend_series = daily_series("""
            SELECT DATE(payment_date) as day, SUM(amount) as total
            FROM payments
            WHERE buyer_id = %s AND payment_status = 'completed'
              AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 13 DAY)
            GROUP BY DATE(payment_date)
        """, (current_user.id,))

        return render_template('buyer_dashboard.html',
                              my_bids=my_bids,
                              watchlist=watchlist,
                              wins=wins,
                              bids_series=bids_series,
                              spend_series=spend_series)
    except Exception as e:
        print(f"Buyer dashboard error: {e}")
        flash('Error loading buyer dashboard', 'danger')
        return redirect(url_for('index'))

# ============================================
# AUCTION MANAGEMENT
# ============================================

@app.route('/create_auction', methods=['GET', 'POST'])
@login_required
def create_auction():
    if current_user.user_type not in ['seller', 'admin']:
        flash('Access denied. Only sellers can create auctions.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title  = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        starting_price = request.form.get('starting_price')
        min_bid_increment = request.form.get('min_bid_increment', 1.00)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not all([title, description, starting_price, start_date, end_date]): # type: ignore
            flash('All fields are required.', 'danger')
            return render_template('create_auction.html', categories=get_categories())
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO auctions (seller_id, title, description, category, starting_price, 
                                    current_price, min_bid_increment, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft')
            """, (current_user.id, title, description, category, starting_price, 
                  starting_price, min_bid_increment, start_date, end_date))
            
            auction_id = cur.lastrowid
            
            # Handle image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                is_primary = True
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                        filename = timestamp + filename
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        
                        cur.execute("""
                            INSERT INTO auction_images (auction_id, image_url, is_primary)
                            VALUES (%s, %s, %s)
                        """, (auction_id, filename, is_primary))
                        is_primary = False
            
            # Update status to active
            cur.execute("UPDATE auctions SET status = 'active' WHERE auction_id = %s", (auction_id,))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Auction created successfully!', 'success')
            return redirect(url_for('auction_details', auction_id=auction_id))
        except Exception as e:
            print(f"Create auction error: {e}")
            flash('Error creating auction. Please try again.', 'danger')
    
    return render_template('create_auction.html', categories=get_categories())

@app.route('/auction/<int:auction_id>')
def auction_details(auction_id):
    update_auction_status()
    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT a.*, u.username, u.first_name, u.last_name, u.email, u.phone
            FROM auctions a
            JOIN users u ON a.seller_id = u.user_id
            WHERE a.auction_id = %s
        """, (auction_id,))
        auction = cur.fetchone()
        
        if not auction:
            flash('Auction not found', 'danger')
            return redirect(url_for('index'))
        
        # Get images
        cur.execute("""
            SELECT * FROM auction_images 
            WHERE auction_id = %s 
            ORDER BY is_primary DESC, uploaded_at ASC
        """, (auction_id,))
        images = cur.fetchall()
        
        # Get bids (removed bids are excluded from the public history)
        cur.execute("""
            SELECT b.*, u.username, u.first_name, u.last_name
            FROM bids b
            JOIN users u ON b.bidder_id = u.user_id
            WHERE b.auction_id = %s AND b.status = 'accepted'
            ORDER BY b.bid_amount DESC
        """, (auction_id,))
        bids = cur.fetchall()
        
        # Check if in watchlist
        in_watchlist = False
        if current_user.is_authenticated:
            cur.execute("""
                SELECT * FROM watchlist 
                WHERE user_id = %s AND auction_id = %s
            """, (current_user.id, auction_id))
            in_watchlist = cur.fetchone() is not None
        
        cur.close()

        return render_template('auction_detail.html',
                              auction=auction,
                              images=images,
                              bids=bids,
                              in_watchlist=in_watchlist)
    except Exception as e:
        print(f"Auction details error: {e}")
        flash('Error loading auction details.', 'danger')
        return redirect(url_for('index'))

@app.route('/place_bid', methods=['POST'])
@login_required
def place_bid():
    if current_user.user_type != 'buyer':
        flash('Only buyers can place bids.', 'danger')
        return redirect(url_for('index'))
    
    auction_id = request.form.get('auction_id')
    bid_amount = float(request.form.get('bid_amount', 0))
    is_auto_bid = request.form.get('is_auto_bid', 'false') == 'true'
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM auctions WHERE auction_id = %s AND status = 'active'", (auction_id,))
        auction = cur.fetchone()
        
        if not auction:
            flash('Auction is not active.', 'danger')
            cur.close()
            return redirect(url_for('auction_details', auction_id=auction_id))
        
        if bid_amount <= auction['current_price']:
            flash(f'Bid must be higher than current price (${auction["current_price"]})', 'danger')
            cur.close()
            return redirect(url_for('auction_details', auction_id=auction_id))
        
        # Check minimum bid increment
        min_bid = auction['current_price'] + auction['min_bid_increment']
        if bid_amount < min_bid:
            flash(f'Minimum bid is ${min_bid}', 'danger')
            cur.close()
            return redirect(url_for('auction_details', auction_id=auction_id))
        
        # Bids are accepted automatically; an admin may remove one later.
        cur.execute("""
            INSERT INTO bids (auction_id, bidder_id, bid_amount, is_auto_bid, status)
            VALUES (%s, %s, %s, %s, 'accepted')
        """, (auction_id, current_user.id, bid_amount, is_auto_bid))
        
        cur.execute("""
            UPDATE auctions 
            SET current_price = %s, total_bids = total_bids + 1
            WHERE auction_id = %s
        """, (bid_amount, auction_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Bid of ${bid_amount} accepted.', 'success')
        return redirect(url_for('auction_details', auction_id=auction_id))
    except Exception as e:
        print(f"Place bid error: {e}")
        flash('Error placing bid. Please try again.', 'danger')
        return redirect(url_for('auction_details', auction_id=auction_id))

# ============================================
# WATCHLIST MANAGEMENT
# ============================================

@app.route('/add_to_watchlist/<int:auction_id>', methods=['POST'])
@login_required
def add_to_watchlist(auction_id):
    if current_user.user_type not in ['buyer', 'admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    try:
        cur = mysql.connection.cursor()
        # Check if already in watchlist
        cur.execute("SELECT * FROM watchlist WHERE user_id = %s AND auction_id = %s", 
                   (current_user.id, auction_id))
        if cur.fetchone():
            flash('Already in watchlist.', 'info')
            cur.close()
            return redirect(url_for('auction_details', auction_id=auction_id))
        
        cur.execute("""
            INSERT INTO watchlist (user_id, auction_id)
            VALUES (%s, %s)
        """, (current_user.id, auction_id))
        mysql.connection.commit()
        cur.close()
        
        flash('Added to watchlist!', 'success')
        return redirect(url_for('auction_details', auction_id=auction_id))
    except Exception as e:
        print(f"Add to watchlist error: {e}")
        flash('Error adding to watchlist.', 'danger')
        return redirect(url_for('auction_details', auction_id=auction_id))

@app.route('/remove_from_watchlist/<int:auction_id>', methods=['POST'])
@login_required
def remove_from_watchlist(auction_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM watchlist WHERE user_id = %s AND auction_id = %s", 
                   (current_user.id, auction_id))
        mysql.connection.commit()
        cur.close()
        
        flash('Removed from watchlist.', 'success')
        return redirect(request.referrer or url_for('buyer_dashboard'))
    except Exception as e:
        print(f"Remove from watchlist error: {e}")
        flash('Error removing from watchlist.', 'danger')
        return redirect(url_for('buyer_dashboard'))

# ============================================
# PAYMENT MANAGEMENT
# ============================================

@app.route('/payments')
@login_required
def payments():
    if current_user.user_type not in ['buyer', 'admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    is_admin = current_user.user_type == 'admin'

    try:
        cur = mysql.connection.cursor()
        sql = """
            SELECT p.*, a.title as auction_title, u.username as seller_username, 
                   u.first_name as seller_first_name, u.last_name as seller_last_name,
                   b.first_name as buyer_first_name, b.last_name as buyer_last_name
            FROM payments p
            JOIN auctions a ON p.auction_id = a.auction_id
            JOIN users u ON p.seller_id = u.user_id
            JOIN users b ON p.buyer_id = b.user_id
        """
        params = ()
        if not is_admin:
            sql += " WHERE p.buyer_id = %s"
            params = (current_user.id,)
        sql += " ORDER BY p.created_at DESC"

        cur.execute(sql, params)
        payments = cur.fetchall()
        cur.close()

        return render_template('payments.html', payments=payments, is_admin=is_admin)
    except Exception as e:
        print(f"Payments error: {e}")
        flash('Error loading payments.', 'danger')
        return render_template('payments.html', payments=[], is_admin=is_admin)

# ============================================
# ADMIN BID MODERATION
# ============================================

@app.route('/admin/bids')
@login_required
def admin_bids():
    """Every bid on the platform, with the removal controls."""
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))

    status = request.args.get('status', 'all')

    try:
        cur = mysql.connection.cursor()
        sql = """
            SELECT b.*, u.username, u.first_name, u.last_name, u.email,
                   a.title as auction_title, a.status as auction_status,
                   r.first_name as removed_by_first_name, r.last_name as removed_by_last_name
            FROM bids b
            JOIN users u ON b.bidder_id = u.user_id
            JOIN auctions a ON b.auction_id = a.auction_id
            LEFT JOIN users r ON b.removed_by = r.user_id
        """
        params = ()
        if status in ('accepted', 'removed'):
            sql += " WHERE b.status = %s"
            params = (status,)
        sql += " ORDER BY b.bid_time DESC LIMIT 300"

        cur.execute(sql, params)
        bids = cur.fetchall()

        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(status = 'accepted') as accepted,
                SUM(status = 'removed') as removed
            FROM bids
        """)
        totals = cur.fetchone()
        cur.close()

        return render_template('admin_bids.html', bids=bids, totals=totals, status=status)
    except Exception as e:
        print(f"Admin bids error: {e}")
        flash('Error loading bids.', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_bid/<int:bid_id>', methods=['POST'])
@login_required
def admin_remove_bid(bid_id):
    """Remove a bid, recording a reason the bidder will see."""
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))

    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('A reason is required so the bidder knows why the bid was removed.', 'danger')
        return redirect(request.referrer or url_for('admin_bids'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT auction_id, status FROM bids WHERE bid_id = %s", (bid_id,))
        bid = cur.fetchone()

        if not bid:
            cur.close()
            flash('Bid not found.', 'warning')
            return redirect(request.referrer or url_for('admin_bids'))

        if bid['status'] == 'removed':
            cur.close()
            flash('That bid has already been removed.', 'info')
            return redirect(request.referrer or url_for('admin_bids'))

        cur.execute("""
            UPDATE bids
            SET status = 'removed', removed_reason = %s, removed_at = NOW(), removed_by = %s
            WHERE bid_id = %s
        """, (reason, current_user.id, bid_id))

        recalculate_auction(cur, bid['auction_id'])
        mysql.connection.commit()
        cur.close()

        flash('Bid removed. The bidder can see your reason on their dashboard.', 'success')
    except Exception as e:
        print(f"Remove bid error: {e}")
        flash('Error removing the bid.', 'danger')

    return redirect(request.referrer or url_for('admin_bids'))

@app.route('/admin/restore_bid/<int:bid_id>', methods=['POST'])
@login_required
def admin_restore_bid(bid_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT auction_id FROM bids WHERE bid_id = %s AND status = 'removed'", (bid_id,))
        bid = cur.fetchone()

        if not bid:
            cur.close()
            flash('Bid not found or not removed.', 'warning')
            return redirect(request.referrer or url_for('admin_bids'))

        cur.execute("""
            UPDATE bids
            SET status = 'accepted', removed_reason = NULL, removed_at = NULL, removed_by = NULL
            WHERE bid_id = %s
        """, (bid_id,))

        recalculate_auction(cur, bid['auction_id'])
        mysql.connection.commit()
        cur.close()

        flash('Bid reinstated.', 'success')
    except Exception as e:
        print(f"Restore bid error: {e}")
        flash('Error reinstating the bid.', 'danger')

    return redirect(request.referrer or url_for('admin_bids'))

# ============================================
# ADMIN PAYMENT CONTROL
# ============================================

@app.route('/admin/raise_invoice/<int:auction_id>', methods=['POST'])
@login_required
def admin_raise_invoice(auction_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT auction_id, seller_id, winner_id, current_price, status
            FROM auctions WHERE auction_id = %s
        """, (auction_id,))
        auction = cur.fetchone()

        if not auction or not auction['winner_id']:
            cur.close()
            flash('That lot has no winning bidder yet.', 'warning')
            return redirect(url_for('admin_dashboard'))

        created = create_invoice(cur, auction['auction_id'], auction['winner_id'],
                                 auction['seller_id'], auction['current_price'])
        mysql.connection.commit()
        cur.close()

        flash('Invoice raised for the winning bidder.' if created
              else 'That lot already has an invoice.', 'success' if created else 'info')
    except Exception as e:
        print(f"Raise invoice error: {e}")
        flash('Error raising the invoice.', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settle_payment/<int:payment_id>', methods=['POST'])
@login_required
def admin_settle_payment(payment_id):
    """Admin records a payment on a bidder's behalf."""
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))

    payment_method = request.form.get('payment_method', 'bank_transfer')
    shipping_address = request.form.get('shipping_address', '').strip()

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE payments
            SET payment_method = %s,
                shipping_address = COALESCE(NULLIF(%s, ''), shipping_address),
                payment_status = 'completed',
                payment_date = NOW(),
                transaction_id = CONCAT('ADM', UNIX_TIMESTAMP(NOW()), FLOOR(RAND()*1000))
            WHERE payment_id = %s AND payment_status = 'pending'
        """, (payment_method, shipping_address, payment_id))

        if cur.rowcount > 0:
            mysql.connection.commit()
            flash('Payment recorded for the bidder.', 'success')
        else:
            flash('Payment not found or already settled.', 'warning')
        cur.close()
    except Exception as e:
        print(f"Admin settle payment error: {e}")
        flash('Error recording the payment.', 'danger')

    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/reopen_payment/<int:payment_id>', methods=['POST'])
@login_required
def admin_reopen_payment(payment_id):
    if current_user.user_type != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE payments
            SET payment_status = 'pending', payment_date = NULL, transaction_id = NULL
            WHERE payment_id = %s AND payment_status = 'completed'
        """, (payment_id,))

        if cur.rowcount > 0:
            mysql.connection.commit()
            flash('Payment reopened as pending.', 'success')
        else:
            flash('Payment not found or already pending.', 'warning')
        cur.close()
    except Exception as e:
        print(f"Admin reopen payment error: {e}")
        flash('Error reopening the payment.', 'danger')

    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/process_payment/<int:payment_id>', methods=['POST'])
@login_required
def process_payment(payment_id):
    if current_user.user_type != 'buyer':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    payment_method = request.form.get('payment_method', 'credit_card')
    shipping_address = request.form.get('shipping_address', '').strip()
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE payments 
            SET payment_method = %s,
                shipping_address = %s,
                payment_status = 'completed',
                payment_date = NOW(),
                transaction_id = CONCAT('TXN', UNIX_TIMESTAMP(NOW()), FLOOR(RAND()*1000))
            WHERE payment_id = %s AND buyer_id = %s AND payment_status = 'pending'
        """, (payment_method, shipping_address, payment_id, current_user.id))
        
        if cur.rowcount > 0:
            mysql.connection.commit()
            flash('Payment processed successfully!', 'success')
        else:
            flash('Payment not found or already processed.', 'warning')
        cur.close()
        
        return redirect(url_for('payments'))
    except Exception as e:
        print(f"Process payment error: {e}")
        flash('Error processing payment.', 'danger')
        return redirect(url_for('payments'))

# ============================================
# SEARCH AND FILTER
# ============================================

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    status = request.args.get('status', 'active')
    
    try:
        cur = mysql.connection.cursor()
        sql = """
            SELECT a.*, u.username, u.first_name, u.last_name,
                   (SELECT image_url FROM auction_images WHERE auction_id = a.auction_id AND is_primary = TRUE LIMIT 1) as primary_image
            FROM auctions a
            LEFT JOIN users u ON a.seller_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if query:
            sql += " AND (a.title LIKE %s OR a.description LIKE %s)"
            search_term = f"%{query}%"
            params.extend([search_term, search_term])
        
        if category:
            sql += " AND a.category = %s"
            params.append(category)
        
        if min_price:
            sql += " AND a.current_price >= %s"
            params.append(min_price)
        
        if max_price:
            sql += " AND a.current_price <= %s"
            params.append(max_price)
        
        if status and status != 'all':
            sql += " AND a.status = %s"
            params.append(status)
        
        sql += " ORDER BY a.created_at DESC"
        
        cur.execute(sql, params)
        auctions = cur.fetchall()
        cur.close()
        
        return render_template('search.html', auctions=auctions, query=query, categories=get_categories())
    except Exception as e:
        print(f"Search error: {e}")
        flash('Error performing search.', 'danger')
        return render_template('search.html', auctions=[], query=query)

# ============================================
# USER PROFILE
# ============================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not first_name or not last_name:
            flash('First name and last name are required.', 'danger')
            return redirect(url_for('profile'))

        try:
            cur = mysql.connection.cursor()

            # Handle avatar upload if provided
            profile_image = current_user.profile_image
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename and allowed_file(file.filename):
                    # Remove old avatar if it exists
                    if current_user.profile_image:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'],
                                                current_user.profile_image)
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
                    filename = f"avatar_{current_user.id}_{int(datetime.now().timestamp())}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    profile_image = filename

            cur.execute("""
                UPDATE users
                SET first_name = %s, last_name = %s, phone = %s, profile_image = %s
                WHERE user_id = %s
            """, (first_name, last_name, phone, profile_image, current_user.id))
            mysql.connection.commit()
            cur.close()

            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.phone = phone
            current_user.profile_image = profile_image

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            print(f"Profile update error: {e}")
            flash('Error updating profile.', 'danger')

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s", (current_user.id,))
        user = cur.fetchone()
        cur.close()
        return render_template('profile.html', user=user)
    except Exception as e:
        print(f"Profile error: {e}")
        flash('Error loading profile.', 'danger')
        return redirect(url_for('index'))

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AUCTION SYSTEM WITH 6 TABLES STARTING...")
    print("="*60)
    print("📊 Tables: users, auctions, auction_images, bids, payments, watchlist")
    print("🗄️  Database: auction_db")
    print("🌐 Server: http://127.0.0.1:5000")
    print("\n📝 Test Accounts:")
    print("   Admin:  admin@auction.com  / password123")
    print("   Seller: john@email.com    / password123")
    print("   Buyer:  jane@email.com    / password123")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)