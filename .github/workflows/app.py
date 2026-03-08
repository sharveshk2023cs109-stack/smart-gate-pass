import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt
import datetime
from functools import wraps
from twilio.rest import Client
from mongoengine import connect
try:
    import certifi
    tls_ca_file = certifi.where()
    print("✓ Certifi certificate bundle located")
except ImportError:
    tls_ca_file = None
    print("⚠ WARNING: certifi package not found. SSL verification might fail.")
from mongoengine.queryset.base import BaseQuerySet
from bson import ObjectId
from mongoengine.errors import DoesNotExist
from models import User, Request, GateHistory, Holiday

app = Flask(__name__)
# Secure key for JWT (minimum 32 bytes for SHA256)
app.config['SECRET_KEY'] = 'smart-gate-pass-secure-key-2026-v1-highly-confidential'

# Twilio Configuration
app.config['TWILIO_SID'] = 'AC668b893d54e49015715ae01ceaeb55a2'
app.config['TWILIO_TOKEN'] = 'e9a06fc5b42a2fb1d9d81a8fbb2c8453'
app.config['TWILIO_PHONE'] = '+14155238886' 

# Using EmailJS for notifications now
app.config['BASE_URL'] = 'http://localhost:5000' # Update for production

# Initialize MongoDB Connection
def init_db():
    try:
        ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"
        
        # Standard connection arguments
        args = {
            'host': ATLAS_URI,
            'serverSelectionTimeoutMS': 10000,
            'connectTimeoutMS': 10000,
            'socketTimeoutMS': 10000,
        }
        
        if tls_ca_file:
            args['tlsCAFile'] = tls_ca_file
        
        # SSL settings for local development/unstable networks
        args['tlsAllowInvalidCertificates'] = True
        
        print(f"⌛ Connecting to MongoDB Atlas (Timeout: 10s)...")
        client = connect(**args)
        
        # Force a connection check
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB Atlas")
        return True
    except Exception as e:
        print("✗ ERROR: Could not connect to MongoDB Atlas.")
        print(f"Details: {e}")
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("1. Check your internet connection.")
        print("2. Ensure your IP is whitelisted in MongoDB Atlas Network Access.")
        print("3. If DNS errors persist, try changing your DNS settings to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare).")
        return False

# Initialize on startup
db_ready = init_db()

CORS(app)
bcrypt = Bcrypt(app)

# Helper to sanitize MongoDB Dict for JSON serialization
def clean_dict(obj):
    if isinstance(obj, dict):
        return {k: clean_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, BaseQuerySet)):
        return [clean_dict(x) for x in obj]
    if hasattr(obj, 'to_mongo'):
        data = obj.to_mongo().to_dict()
        if isinstance(obj, Request):
            try:
                if obj.student:
                    data['student'] = {
                        'id': str(obj.student.id),
                        'photo': obj.student.photo
                    }
            except DoesNotExist:
                data['student'] = None
        if isinstance(obj, User):
            data['photo'] = obj.photo
        return clean_dict(data)
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj

# SMTP imports removed - using EmailJS on frontend

def get_notification_payload(req, recipient_email, recipient_role):
    """Generates data for EmailJS notification on the frontend."""
    if not recipient_email:
        return None

    # Generate Action Token (Valid for 24 hours)
    token = jwt.encode({
        'req_id': str(req.id),
        'role': recipient_role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    base_url = app.config['BASE_URL']
    
    return {
        'recipient_email': recipient_email,
        'recipient_role': recipient_role.upper(),
        'student_name': req.student_name,
        'type': req.type,
        'duration': f"{req.from_date} to {req.to_date} ({req.days} days)",
        'reason': req.reason,
        'status': req.status,
        'approve_link': f"{base_url}/api/requests/email-action/{token}/approve" if recipient_role != 'student' else '',
        'reject_link': f"{base_url}/api/requests/email-action/{token}/reject" if recipient_role != 'student' else ''
    }

# WhatsApp Notification Helper
def send_whatsapp_notification(phone, name, outing_time):
    if not phone or phone == 'None':
        return
    
    sid = app.config.get('TWILIO_SID')
    token = app.config.get('TWILIO_TOKEN')
    from_whatsapp = app.config.get('TWILIO_PHONE')

    if not sid or 'YOUR' in sid:
        print(f"⚠ Skipping WhatsApp: Twilio credentials not configured. (To: {phone})")
        return

    try:
        client = Client(sid, token)
        body = f"Smart Gate Pass: Your child {name} has left the campus at {outing_time}."
        message = client.messages.create(
            from_=f"whatsapp:{from_whatsapp}",
            body=body,
            to=f"whatsapp:{phone}"
        )
        print(f"✓ WhatsApp notification sent to {phone}: {message.sid}")
    except Exception as e:
        print(f"✗ Failed to send WhatsApp notification to {phone}: {e}")

# Authentication Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            if not db_ready:
                return jsonify({'message': 'Database offline!'}), 503
            current_user = User.objects(email=data['email']).first()
            if not current_user:
                print(f"✗ Auth Failed: User {data.get('email')} no longer exists")
                return jsonify({'message': 'User no longer exists!'}), 401
        except jwt.ExpiredSignatureError:
            print("✗ Auth Failed: Token expired")
            return jsonify({'message': 'Session expired. Please login again.'}), 401
        except jwt.InvalidTokenError:
            print("✗ Auth Failed: Invalid token")
            return jsonify({'message': 'Invalid session. Please login again.'}), 401
        except Exception as e:
            print(f"✗ Auth Failed: {str(e)}")
            return jsonify({'message': 'Authentication failed!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Static File Serving
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/health')
def health_check():
    try:
        # Check if DB is connected
        from models import User
        count = User.objects.count()
        return jsonify({'status': 'healthy', 'db': 'connected', 'user_count': count})
    except Exception as e:
        return jsonify({'status': 'degraded', 'db': 'error', 'details': str(e)}), 200

# API Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    if not db_ready:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 503
    data = request.get_json()
    if User.objects(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    
    role = data.get('role')
    dept = data.get('dept')
    year = data.get('year')
    section = data.get('section')

    # Restricted role check
    if role in ['admin', 'gate']:
        return jsonify({'success': False, 'message': 'Restricted accounts cannot be registered manually.'}), 403

    # Scope uniqueness checks
    if role == 'hod':
        if User.objects(role='hod', dept=dept).first():
             return jsonify({'success': False, 'message': f"An HOD is already registered for {dept}"}), 400
    elif role == 'staff':
        if User.objects(role='staff', dept=dept, year=year, section=section).first():
             return jsonify({'success': False, 'message': "A Class Advisor is already registered for this scope"}), 400
    elif role == 'warden':
        if User.objects(role='warden', year=year).first():
             return jsonify({'success': False, 'message': f"A Warden is already registered for Year {year}"}), 400

    user = User(
        name=data['name'],
        email=data['email'],
        password=data['password'],
        role=role,
        dept=dept,
        year=year,
        semester=data.get('semester'),
        section=section,
        photo=data.get('photo'),
        parent_mobile=data.get('parent_mobile')
    )
    user.hash_password()
    user.save()
    return jsonify({'success': True, 'message': 'User registered successfully'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    if not db_ready:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 503
    data = request.get_json()
    user = User.objects(email=data['email']).first()
    
    if not user:
        print(f"✗ Login Failed: Email not found - {data['email']}")
        return jsonify({'success': False, 'message': 'Email not registered'}), 401
        
    if not user.check_password(data['password']):
        print(f"✗ Login Failed: Incorrect password for {data['email']}")
        return jsonify({'success': False, 'message': 'Incorrect password'}), 401

    token = jwt.encode({
        'email': user.email,
        'role': user.role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    print(f"✓ Login Success: {user.email} ({user.role})")
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'dept': user.dept,
            'year': user.year,
            'semester': user.semester,
            'section': user.section,
            'photo': user.photo,
            'parent_mobile': user.parent_mobile
        }
    })

@app.route('/api/requests', methods=['GET', 'POST'])
@token_required
def manage_requests(current_user):
    if request.method == 'POST':
        data = request.get_json()
        new_request = Request(
            student=current_user,
            student_name=current_user.name,
            student_email=current_user.email,
            dept=current_user.dept,
            year_sem_sec=f"Year {current_user.year} / Sem {current_user.semester} / Sec {current_user.section}",
            type=data['type'],
            resident_type=data['resident_type'],
            reason=data['reason'],
            from_date=data['from_date'],
            to_date=data['to_date'],
            days=data['days'],
            document=data.get('document')
        )
        new_request.save()

        # Holiday Bypass Logic
        try:
            start_date = datetime.datetime.strptime(new_request.from_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(new_request.to_date, "%Y-%m-%d")
            delta = end_date - start_date
            dates_to_check = [(start_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
            
            # Check if EVERYTHING in the requested range is a holiday
            holiday_count = Holiday.objects(date__in=dates_to_check).count()
            
            if holiday_count == len(dates_to_check) and new_request.resident_type == 'Hosteller':
                new_request.status = 'Pending Warden'
                new_request.save()
                print(f"ℹ Total Holiday Period detected for {new_request.student_name} (Hosteller). Bypassing Advisor and HOD.")
        except Exception as e:
            print(f"Error checking holidays during submission: {e}")

        # Notify Staff (Class Advisor) - Now via Frontend EmailJS
        notification = None
        staff = User.objects(role='staff', dept=current_user.dept, year=current_user.year, section=current_user.section).first()
        if staff:
            if new_request.status == 'Pending': # Normal flow
                notification = get_notification_payload(new_request, staff.email, 'staff')
            elif new_request.status == 'Pending Warden': # Holiday bypass flow
                warden = User.objects(role='warden', year=current_user.year).first()
                if warden:
                    notification = get_notification_payload(new_request, warden.email, 'warden')

        return jsonify({'success': True, 'message': 'Request submitted', 'notification': notification})
    
    if current_user.role == 'student':
        requests = Request.objects(student_email=current_user.email).order_by('-created_at')
    elif current_user.role == 'staff':
        requests = Request.objects(status='Pending', dept__iexact=current_user.dept, year_sem_sec__icontains=f"Year {current_user.year}").filter(year_sem_sec__icontains=f"Sec {current_user.section}")
    elif current_user.role == 'hod':
        requests = Request.objects(status='Recommended', dept__iexact=current_user.dept)
    elif current_user.role == 'warden':
        requests = Request.objects(status='Pending Warden', year_sem_sec__icontains=f"Year {current_user.year}")
    else:
        requests = Request.objects().order_by('-created_at')

    # Convert to list of dicts for injection
    request_list = clean_dict(requests)
    
    # Inject history counts for Student, Staff, HOD and Warden
    if current_user.role in ['student', 'staff', 'hod', 'warden']:
        for req in request_list:
            email = req.get('student_email')
            if email:
                req['leave_count'] = Request.objects(student_email=email, status='Approved', type='Leave').count()
                req['od_count'] = Request.objects(student_email=email, status='Approved', type='On Duty').count()
                
    return jsonify(request_list)

@app.route('/api/holidays', methods=['GET', 'POST'])
@token_required
def manage_holidays(current_user):
    if request.method == 'POST':
        if current_user.role != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
        data = request.get_json()
        if Holiday.objects(date=data['date']).first():
            return jsonify({'success': False, 'message': 'Holiday already exists for this date'}), 400
        holiday = Holiday(date=data['date'], reason=data['reason'])
        holiday.save()
        return jsonify({'success': True, 'message': 'Holiday added'})
    
    holidays = Holiday.objects().order_by('date')
    return jsonify(clean_dict(holidays))

@app.route('/api/holidays/<id>', methods=['DELETE'])
@token_required
def delete_holiday(current_user, id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    holiday = Holiday.objects(id=id).first()
    if holiday:
        holiday.delete()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Holiday not found'}), 404



@app.route('/api/requests/<req_id>/status', methods=['PUT'])
@token_required
def update_status(current_user, req_id):
    data = request.get_json()
    req = Request.objects(id=req_id).first()
    if not req:
        return jsonify({'success': False, 'message': 'Request not found'}), 404
    
    role = current_user.role
    decision = data['decision']
    
    if decision == 'reject':
        req.status = f'Rejected by {role.upper()}'
    else:
        if role == 'staff':
            req.status = 'Recommended'
            req.staff_approval = True
        elif role == 'hod':
            if req.resident_type == 'Hosteller':
                req.status = 'Pending Warden'
            else:
                req.status = 'Approved'
                req.approved_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                # 6-Hour Validity
                req.expiry_timestamp = int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=6)).timestamp() * 1000)
            req.hod_approval = True
        elif role == 'warden':
            req.status = 'Approved'
            req.warden_approval = True
            req.approved_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            # 6-Hour Validity
            req.expiry_timestamp = int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=6)).timestamp() * 1000)
            
    req.save()

    # If approved, determine who to notify next
    notification = None
    if decision == 'approve':
        if role == 'staff':
            hod = User.objects(role='hod', dept=req.dept).first()
            if hod:
                notification = get_notification_payload(req, hod.email, 'hod')
        elif role == 'hod':
            if req.resident_type == 'Hosteller':
                warden = User.objects(role='warden', year=req.student.year).first()
                if warden:
                    notification = get_notification_payload(req, warden.email, 'warden')
            else:
                # Final Approval for Day Scholar
                notification = get_notification_payload(req, req.student_email, 'student')
        elif role == 'warden':
            # Final Approval for Hosteller
            notification = get_notification_payload(req, req.student_email, 'student')
    else:
        # Rejection - Notify Student
        notification = get_notification_payload(req, req.student_email, 'student')

    return jsonify({'success': True, 'notification': notification})

@app.route('/api/requests/email-action/<token>/<decision>')
def email_action(token, decision):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        req_id = data['req_id']
        role = data['role']
        
        req = Request.objects(id=req_id).first()
        if not req:
            return "<h3>Error: Request not found or already deleted.</h3>", 404
        
        # Check if already processed
        if decision == 'approve':
            if role == 'staff' and req.staff_approval:
                return "<h3>Info: This request was already recommended by Staff.</h3>"
            if role == 'hod' and req.hod_approval:
                return "<h3>Info: This request was already approved by HOD.</h3>"
            if role == 'warden' and req.warden_approval:
                return "<h3>Info: This request was already approved by Warden.</h3>"
        
        # Apply Logic (Backend processing only - no notification sent from here)
        if decision == 'reject':
            req.status = f'Rejected by {role.upper()}'
        else:
            if role == 'staff':
                req.status = 'Recommended'
                req.staff_approval = True
            elif role == 'hod':
                if req.resident_type == 'Hosteller':
                    req.status = 'Pending Warden'
                else:
                    req.status = 'Approved'
                    req.approved_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                    req.expiry_timestamp = int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=6)).timestamp() * 1000)
                req.hod_approval = True
            elif role == 'warden':
                req.status = 'Approved'
                req.warden_approval = True
                req.approved_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                req.expiry_timestamp = int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=6)).timestamp() * 1000)
        
        req.save()
        return f"<h3>Successfully {decision}d the request as {role.upper()}!</h3>"
        
    except jwt.ExpiredSignatureError:
        return "<h3>Error: This link has expired.</h3>", 400
    except jwt.InvalidTokenError:
        return "<h3>Error: Invalid link.</h3>", 400
    except Exception as e:
        return f"<h3>Error: {str(e)}</h3>", 500

@app.route('/api/gate/record', methods=['POST'])
@token_required
def gate_record(current_user):
    if current_user.role != 'gate':
        return jsonify({'message': 'Unauthorized'}), 403
    data = request.get_json()
    req_id = data.get('id')
    
    # Try to get most accurate details from the original request
    req = Request.objects(id=req_id).first() if req_id and len(req_id) == 24 else None
    
    # Prevent Duplicate Recordings (Race Condition Mitigation)
    recent_check = GateHistory.objects(
        request_id=str(req_id),
        created_at__gte=datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - datetime.timedelta(seconds=10)
    ).first()
    
    if recent_check:
        print(f"ℹ Duplicate Gate Entry Blocked for Request: {req_id}")
        return jsonify({'success': True, 'record': clean_dict(recent_check), 'message': 'Duplicate scan ignored'})

    history = GateHistory(
        request_id=str(req_id),
        name=req.student_name if req else data.get('name'),
        dept=req.dept if req else data.get('dept'),
        year_sem_sec=req.year_sem_sec if req else data.get('year_sem_sec'),
        outing_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    history.save()

    # Trigger WhatsApp Notification
    if req and req.student and req.student.parent_mobile:
        send_whatsapp_notification(
            req.student.parent_mobile,
            req.student_name,
            history.outing_time
        )
    elif not req:
        # Fallback if student doc is missing but we have name from history
        print(f"ℹ Could not send WhatsApp for {data.get('name')}: Student document or mobile number missing.")

    return jsonify({'success': True, 'record': clean_dict(history)})

@app.route('/api/gate/history', methods=['GET'])
@token_required
def gate_history(current_user):
    if current_user.role != 'gate':
        return jsonify({'message': 'Unauthorized'}), 403
    history = GateHistory.objects().order_by('-created_at')
    return jsonify(clean_dict(history))

@app.route('/api/gate/history/clear', methods=['POST'])
@token_required
def clear_gate_history(current_user):
    if current_user.role != 'gate':
        return jsonify({'message': 'Unauthorized'}), 403
    GateHistory.objects().delete()
    return jsonify({'success': True})

@app.route('/api/admin/users', methods=['GET'])
@token_required
def get_users(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    users = User.objects(role__ne='admin')
    return jsonify(clean_dict(users))

@app.route('/api/admin/users/<email>', methods=['PUT', 'DELETE'])
@token_required
def manage_user(current_user, email):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    user = User.objects(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if request.method == 'DELETE':
        user.delete()
        return jsonify({'success': True})
    
    if request.method == 'PUT':
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.dept = data.get('dept', user.dept)
        user.year = data.get('year', user.year)
        user.semester = data.get('semester', user.semester)
        user.section = data.get('section', user.section)
        user.parent_mobile = data.get('parent_mobile', user.parent_mobile)
        user.save()
        return jsonify({'success': True})

if __name__ == '__main__':
    # Initialize Default Users
    defaults = [
        {'name': 'System Admin', 'email': 'admin@portal.edu', 'password': 'adminportal123', 'role': 'admin'},
        {'name': 'Gate Security', 'email': 'gate@portal.edu', 'password': 'gateportal123', 'role': 'gate'}
    ]
    try:
        for def_user in defaults:
            if not User.objects(email=def_user['email']).first():
                user = User(
                    name=def_user['name'],
                    email=def_user['email'],
                    password=def_user['password'],
                    role=def_user['role']
                )
                user.hash_password()
                user.save()
                print(f"Default {def_user['role']} created: {def_user['email']}")
    except Exception as init_e:
        print(f"⚠ WARNING: Could not initialize default users: {init_e}")
    
    # Run server last (this blocks)
    app.run(debug=True, port=5000)
