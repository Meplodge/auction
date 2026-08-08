from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import re

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
    try:
        cur = mysql.connection.cursor()
        # Close expired auctions
        cur.execute("""
            UPDATE auctions 
            SET status = 'closed' 
            WHERE end_date < NOW() AND status = 'active'
        """)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print(f"Error updating auction status: {e}")

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
        
        cur.execute("SELECT COUNT(*) as total FROM bids")
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
        
        # Recent activity
        cur.execute("""
            SELECT b.*, u.username, a.title as auction_title
            FROM bids b
            JOIN users u ON b.bidder_id = u.user_id
            JOIN auctions a ON b.auction_id = a.auction_id
            ORDER BY b.bid_time DESC
            LIMIT 10
        """)
        recent_bids = cur.fetchall()
        
        # Recent users
        cur.execute("""
            SELECT * FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_users = cur.fetchall()
        
        cur.close()
        
        return render_template('admin_dashboard.html', 
                              stats=stats, 
                              recent_bids=recent_bids,
                              recent_users=recent_users)
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
                   (SELECT COUNT(*) FROM bids WHERE auction_id = a.auction_id) as bid_count,
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
                (SELECT COUNT(*) FROM bids WHERE auction_id IN (SELECT auction_id FROM auctions WHERE seller_id = %s)) as total_bids
            FROM auctions
            WHERE seller_id = %s
        """, (current_user.id, current_user.id))
        stats = cur.fetchone()
        cur.close()
        
        return render_template('seller_dashboard.html', auctions=auctions, stats=stats)
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

        # My bids
        cur.execute("""
            SELECT b.*, a.title, a.status as auction_status, a.end_date,
                   (SELECT MAX(bid_amount) FROM bids WHERE auction_id = b.auction_id) as highest_bid
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

        return render_template('buyer_dashboard.html',
                              my_bids=my_bids,
                              watchlist=watchlist,
                              wins=wins)
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
        
        # Get bids
        cur.execute("""
            SELECT b.*, u.username, u.first_name, u.last_name
            FROM bids b
            JOIN users u ON b.bidder_id = u.user_id
            WHERE b.auction_id = %s
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
        
        cur.execute("""
            INSERT INTO bids (auction_id, bidder_id, bid_amount, is_auto_bid)
            VALUES (%s, %s, %s, %s)
        """, (auction_id, current_user.id, bid_amount, is_auto_bid))
        
        cur.execute("""
            UPDATE auctions 
            SET current_price = %s, total_bids = total_bids + 1
            WHERE auction_id = %s
        """, (bid_amount, auction_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Bid of ${bid_amount} placed successfully!', 'success')
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
    if current_user.user_type != 'buyer':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT p.*, a.title as auction_title, u.username as seller_username, 
                   u.first_name as seller_first_name, u.last_name as seller_last_name
            FROM payments p
            JOIN auctions a ON p.auction_id = a.auction_id
            JOIN users u ON p.seller_id = u.user_id
            WHERE p.buyer_id = %s
            ORDER BY p.created_at DESC
        """, (current_user.id,))
        payments = cur.fetchall()
        cur.close()
        
        return render_template('payments.html', payments=payments)
    except Exception as e:
        print(f"Payments error: {e}")
        flash('Error loading payments.', 'danger')
        return render_template('payments.html', payments=[])

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
            cur.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, phone = %s
                WHERE user_id = %s
            """, (first_name, last_name, phone, current_user.id))
            mysql.connection.commit()
            cur.close()
            
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.phone = phone
            
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