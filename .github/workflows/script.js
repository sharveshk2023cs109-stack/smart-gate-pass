const BASE_URL = window.location.port === '5000' ? '/api' : 'http://127.0.0.1:5000/api';
const TOKEN_KEY = 'gate_pass_token';
const SESSION_KEY = 'gate_pass_session';
const THEME_KEY = 'gate_pass_theme';
let isAlertingAuth = false;

// EmailJS Configuration
const EMAILJS_PUBLIC_KEY = 'Nops5HUDAbegU0Tk2';
const EMAILJS_SERVICE_ID = 'service_i3l2vwb';
const EMAILJS_TEMPLATE_ID = 'template_dd97vgw';

if (typeof emailjs !== 'undefined') {
    emailjs.init(EMAILJS_PUBLIC_KEY);
}

// Theme Logic
function toggleTheme() {
    const body = document.body;
    const isLight = body.classList.toggle('light-theme');
    localStorage.setItem(THEME_KEY, isLight ? 'light' : 'dark');
    updateThemeToggleUI();
}

function initTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
}

function updateThemeToggleUI() {
    const toggleIcon = document.getElementById('theme-toggle-icon');
    if (toggleIcon) {
        const isLight = document.body.classList.contains('light-theme');
        toggleIcon.className = isLight ? 'fas fa-moon' : 'fas fa-sun';
    }
}

initTheme();

// Helper for Authenticated API Requests
async function apiRequest(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = token.trim();

    const options = { method, headers };
    if (data) options.body = JSON.stringify(data);

    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, options);

        let result;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            result = await response.json();
        } else {
            const text = await response.text();
            console.error("Non-JSON response:", text);
            return { success: false, message: `Server error (${response.status})` };
        }

        if (response.status === 401) {
            // If it's not the login page, clear session and alert with the specific reason
            if (!endpoint.includes('/auth/login') && !isAlertingAuth) {
                isAlertingAuth = true;
                logout();
                alert(result.message || 'Your session has expired. Please login again.');
                setTimeout(() => isAlertingAuth = false, 2000);
            }
            return { success: false, message: result.message || 'Unauthorized' };
        }
        return result;
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, message: 'Server connection failed' };
    }
}

// User Management Logic
async function registerUser(userData) {
    return await apiRequest('/auth/register', 'POST', userData);
}

async function loginUser(email, password) {
    const result = await apiRequest('/auth/login', 'POST', { email, password });
    if (result.success) {
        localStorage.setItem(TOKEN_KEY, result.token);
        localStorage.setItem(SESSION_KEY, JSON.stringify(result.user));
    }
    return result;
}

function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    window.location.href = 'index.html';
}

function getCurrentUser() {
    return JSON.parse(localStorage.getItem(SESSION_KEY));
}

function checkAuth(requiredRole) {
    initTheme();
    const user = getCurrentUser();
    const path = window.location.pathname;
    const page = path.split("/").pop() || 'index.html';

    console.log('CheckAuth:', { page, userRole: user?.role, requiredRole });

    if (!user) {
        if (page !== 'index.html' && page !== 'register.html' && page !== 'login.html') {
            window.location.href = 'index.html';
        }
        return;
    }

    if (page === 'index.html' || page === 'login.html' || page === 'register.html') {
        window.location.href = `${user.role}.html`;
        return;
    }

    if (requiredRole && user.role !== requiredRole) {
        alert('Unauthorized access');
        window.location.href = 'index.html';
    }
}

// Request Management Logic
async function getRequests() {
    return await apiRequest('/requests');
}

async function saveRequest(request) {
    const result = await apiRequest('/requests', 'POST', request);
    if (result.success) {
        if (result.notification) {
            await sendNotification(result.notification);
        }
        alert('Request submitted successfully!');
        window.location.reload();
    } else {
        alert(result.message);
    }
}

async function updateRequestStatus(id, role, decision) {
    const result = await apiRequest(`/requests/${id}/status`, 'PUT', { decision });
    if (result.success) {
        if (result.notification) {
            await sendNotification(result.notification);
        }
        window.location.reload();
    } else {
        alert(result.message);
    }
}

async function sendNotification(notificationData) {
    if (!notificationData || typeof emailjs === 'undefined') {
        console.warn('Skipping notification: Payload empty or EmailJS not loaded');
        return;
    }

    try {
        console.log('Sending EmailJS Notification:', notificationData);
        // Use placeholders if real keys not provided yet
        const serviceId = EMAILJS_SERVICE_ID === 'YOUR_SERVICE_ID' ? '' : EMAILJS_SERVICE_ID;
        const templateId = EMAILJS_TEMPLATE_ID === 'YOUR_TEMPLATE_ID' ? '' : EMAILJS_TEMPLATE_ID;

        if (!serviceId || !templateId) {
            console.warn('EmailJS IDs not configured yet.');
            return;
        }

        await emailjs.send(serviceId, templateId, {
            recipient_email: notificationData.recipient_email,
            recipient_role: notificationData.recipient_role,
            student_name: notificationData.student_name,
            type: notificationData.type,
            duration: notificationData.duration,
            reason: notificationData.reason,
            status: notificationData.status || 'Pending Approval',
            approve_link: notificationData.approve_link,
            reject_link: notificationData.reject_link
        });
        console.log('✓ EmailJS Notification Sent');
    } catch (error) {
        console.error('✗ EmailJS Failed:', error);
        alert('EmailJS Error: ' + (error.text || error.message || 'Unknown error'));
    }
}

// Form Handlers
async function handleStudentSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {};

    // Convert FormData to object, skipping the file for now
    formData.forEach((value, key) => {
        if (key !== 'document') data[key] = value;
    });

    // Handle File Upload ONLY if a file is actually selected
    const fileInput = e.target.querySelector('input[name="document"]');
    if (fileInput && fileInput.files && fileInput.files[0]) {
        try {
            const file = fileInput.files[0];
            const base64 = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = (err) => reject(err);
                reader.readAsDataURL(file);
            });
            data.document = base64;
        } catch (fileError) {
            console.error('File Read Error:', fileError);
            alert('Failed to process document. Please try again or skip.');
            return;
        }
    }

    if (data.from_date && data.to_date) {
        const start = new Date(data.from_date);
        const end = new Date(data.to_date);
        const diff = Math.abs(end - start);
        const days = Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1;
        data.days = days;
    }

    await saveRequest(data);
}

async function handleRegister(e) {
    e.preventDefault();
    // Clear any old session before starting registration
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);

    const formData = new FormData(e.target);
    const data = {};
    formData.forEach((value, key) => {
        if (key !== 'user_photo') data[key] = value;
    });

    // Handle User Photo
    const photoInput = e.target.querySelector('input[name="user_photo"]');
    if (photoInput && photoInput.files && photoInput.files[0]) {
        try {
            const file = photoInput.files[0];
            const base64 = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = (err) => reject(err);
                reader.readAsDataURL(file);
            });
            data.photo = base64;
        } catch (err) {
            console.error('Photo processing failed:', err);
        }
    }

    console.log('Registration Attempt:', data);

    // Handle Parent Mobile Number for Students
    if (data.role === 'student' && data.parent_mobile) {
        data.parent_mobile = '+91' + data.parent_mobile;
    }

    const result = await registerUser(data);
    if (result.success) {
        alert('Registration successful! Please login.');
        window.location.href = 'index.html';
    } else {
        alert(result.message);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const { email, password } = Object.fromEntries(formData.entries());
    const activeTab = document.querySelector('.tab-btn.active').dataset.portal;

    console.log('Login Attempt:', { email, activeTab });

    const result = await loginUser(email, password);
    console.log('Login Result:', result);

    if (result.success) {
        const userRole = result.user.role;
        console.log('Redirecting to:', `${userRole}.html`);

        // Strict Role Enforcement
        if (activeTab === 'gate' && userRole !== 'gate') {
            alert('Access Denied: This tab is for Gate Security only.');
            return logout();
        }
        if (activeTab === 'admin' && userRole !== 'admin') {
            alert('Access Denied: This tab is for System Administrators only.');
            return logout();
        }
        if (activeTab === 'portal' && (userRole === 'admin' || userRole === 'gate')) {
            alert('Access Denied: Please use the appropriate login tab.');
            return logout();
        }

        window.location.href = `${userRole}.html`;
    } else {
        alert(result.message);
    }
}

function switchLoginTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');

    const desc = document.getElementById('login-desc');
    if (tab === 'gate') desc.textContent = 'Security Personnel: Please login to record gate entries.';
    else if (tab === 'admin') desc.textContent = 'System Administrators: Access your management dashboard.';
    else desc.textContent = 'Please enter your credentials to access your portal.';
}

// Render Logic
async function renderStudentRequests(existingRequests = null) {
    const container = document.getElementById('student-requests-container');
    if (!container) return;

    // Use provided requests or fetch new ones
    const response = existingRequests || await getRequests();
    if (!Array.isArray(response)) return;

    if (response.length === 0) {
        container.innerHTML = '<p style="text-align:center; color: var(--text-muted); margin-top:1rem">No requests found.</p>';
        return;
    }

    container.innerHTML = `
        <h2 style="margin: 2rem 0 1.25rem; font-size: 1.25rem; color: var(--text-main); font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-history" style="color: var(--primary);"></i> My Recent Permissions
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.25rem;">
        ${response.map(req => {
        const data = req;
        const statusClass = getStatusClass(data.status);
        return `
            <div class="request-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div style="flex: 1;">
                        <h4 style="color: var(--text-main); margin: 0; font-size: 0.95rem; font-weight: 700;">${data.reason}</h4>
                        <p style="font-size: 0.7rem; color: var(--text-muted); margin-top: 2px;">${new Date(data.created_at.$date || data.created_at).toLocaleDateString()}</p>
                    </div>
                    <span class="status-badge ${statusClass}">${data.status.toUpperCase()}</span>
                </div>
                
                <div style="background: var(--bg-dark); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-light); font-size: 0.8rem; margin-bottom: 1rem;">
                    <p style="margin: 0 0 4px; color: var(--text-muted);"><strong>Type:</strong> <span style="color: var(--text-main)">${data.type}</span></p>
                    <p style="margin: 0; color: var(--text-muted);"><strong>Dates:</strong> <span style="color: var(--primary); font-weight: 600;">${data.from_date}</span> to <span style="color: var(--primary); font-weight: 600;">${data.to_date}</span></p>
                </div>

                <div style="margin-top: auto; padding-top: 0.75rem; border-top: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; gap: 0.35rem;">
                        <div title="Staff" style="width: 24px; height: 24px; border-radius: 4px; background: ${data.staff_approval ? 'var(--success)' : 'var(--bg-dark)'}; color: ${data.staff_approval ? 'white' : 'var(--text-muted)'}; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; border: 1px solid var(--border-light);">S</div>
                        <div title="HOD" style="width: 24px; height: 24px; border-radius: 4px; background: ${data.hod_approval ? 'var(--success)' : 'var(--bg-dark)'}; color: ${data.hod_approval ? 'white' : 'var(--text-muted)'}; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; border: 1px solid var(--border-light);">H</div>
                        ${data.resident_type !== 'Day Scholar' ? `<div title="Warden" style="width: 24px; height: 24px; border-radius: 4px; background: ${data.warden_approval ? 'var(--success)' : 'var(--bg-dark)'}; color: ${data.warden_approval ? 'white' : 'var(--text-muted)'}; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; border: 1px solid var(--border-light);">W</div>` : ''}
                    </div>
                    ${data.status === 'Approved' ? `<button onclick="printLeaveForm('${data._id?.$oid || data._id || data.id}')" class="print-btn" style="padding: 0.4rem 0.75rem;"><i class="fas fa-print"></i></button>` : ''}
                </div>
            </div>
        `;
    }).join('')}
        </div>
    `;
}

async function printLeaveForm(requestId) {
    const requests = await getRequests();
    const req = requests.find(r => (r._id?.$oid || r._id || r.id) === requestId);
    if (!req) return;

    const expiryTimeFormatted = req.expiry_timestamp ? new Date(req.expiry_timestamp).toLocaleString('en-IN', {
        day: 'numeric', month: 'numeric', year: 'numeric',
        hour: 'numeric', minute: 'numeric', second: 'numeric', hour12: true
    }) : 'N/A';

    const isExpired = req.expiry_timestamp && Date.now() > req.expiry_timestamp;

    // Compact QR Data
    const reqId = req._id?.$oid || req._id || req.id;
    const qrData = `PASS|${reqId}|${req.student_name}|${req.dept}|${req.year_sem_sec}|${req.type}|EXP:${expiryTimeFormatted}`;
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(qrData)}`;

    const printWindow = window.open('', '_blank');
    const html = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gate Pass - ${req.student_name}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');
                body { font-family: 'Roboto', sans-serif; padding: 20px; background: #f0f0f0; }
                .gate-pass { border: 2px solid #000; padding: 40px; max-width: 750px; margin: 0 auto; position: relative; background: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 15px; margin-bottom: 30px; }
                .header h1 { margin: 0; font-size: 28px; font-weight: 900; letter-spacing: 2px; }
                .header p { margin: 5px 0 0; font-size: 18px; font-weight: 700; color: #333; }
                .content-row { display: flex; align-items: baseline; margin-bottom: 25px; }
                .label { font-weight: 900; font-size: 18px; width: 180px; color: #222; }
                .value { flex: 1; font-size: 18px; border-bottom: 1.5px dashed #666; padding-left: 10px; padding-bottom: 2px; color: #333; }
                .approved-stamp { position: absolute; top: 100px; right: 40px; border: 5px solid #4CAF50; color: #4CAF50; padding: 10px 30px; font-size: 32px; font-weight: 900; transform: rotate(-15deg); opacity: 0.8; text-transform: uppercase; border-radius: 12px; letter-spacing: 3px; }
                .footer { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 50px; }
                .qr-container { text-align: center; }
                .approval-info { text-align: right; font-size: 11px; color: #666; margin-bottom: 40px; font-style: italic; }
                .signature-section { display: flex; gap: 40px; }
                .sig { text-align: center; }
                .sig-line { border-top: 2px solid #000; width: 160px; margin-bottom: 5px; }
                @media print { body { background: none; padding: 0; } .gate-pass { border: 2px solid #000; box-shadow: none; } .print-btn { display: none; } }
            </style>
        </head>
        <body>
            <div class="gate-pass">
                ${isExpired ? '<div class="approved-stamp" style="border-color:#F44336; color:#F44336;">EXPIRED</div>' : '<div class="approved-stamp">APPROVED</div>'}
                <div class="header">
                    <h1>SMART GATE PASS SYSTEM</h1>
                    <p>Student Leave/OD Permission Form</p>
                </div>
                <div class="content-row"><span class="label">Name:</span><span class="value">${req.student_name}</span></div>
                <div class="content-row"><span class="label">Department:</span><span class="value">${req.dept}</span></div>
                <div class="content-row"><span class="label">Year / Sem / Sec:</span><span class="value">${req.year_sem_sec}</span></div>
                <div class="content-row"><span class="label">Category:</span><span class="value">${req.resident_type}</span></div>
                <div class="content-row"><span class="label">Type:</span><span class="value">${req.type}</span></div>
                <div class="content-row"><span class="label">Duration:</span><span class="value">${req.from_date} to ${req.to_date} (${req.days} Day/s)</span></div>
                <div class="content-row"><span class="label">Reason:</span><span class="value">${req.reason}</span></div>
                <div class="approval-info">
                    Digitally Approved On: ${new Date(req.approved_at.$date || req.approved_at).toLocaleString()}<br>
                    <span style="color: ${isExpired ? '#F44336' : '#E91E63'}; font-weight: bold; font-size: 14px;">
                        Valid Until: ${expiryTimeFormatted} ${isExpired ? '(EXPIRED)' : ''}
                    </span>
                </div>
                <div class="footer">
                    <div class="qr-container"><img src="${qrUrl}" width="140"><p>Scan to verify authenticity</p></div>
                    <div class="signature-section">
                        <div class="sig"><div class="sig-line"></div><span style="font-weight:900">Staff Signature</span></div>
                        <div class="sig"><div class="sig-line"></div><span style="font-weight:900">HOD Signature</span></div>
                    </div>
                </div>
            </div>
            <div style="text-align:center; margin-top:20px;">
                ${isExpired ? '<p style="color:#F44336; font-weight:bold;">This pass has expired and cannot be printed for use.</p>' : '<button class="print-btn" onclick="window.print()" style="padding: 10px 30px; font-size: 16px; background: #2196F3; color: white; border: none; border-radius: 5px; cursor: pointer;">Print Pass</button>'}
            </div>
        </body>
        </html>
    `;
    printWindow.document.write(html);
    printWindow.document.close();
}

function getStatusClass(status) {
    if (status === 'Approved') return 'badge-approved';
    if (status.includes('Rejected')) return 'badge-rejected';
    return 'badge-pending';
}

window.currentView = 'pending';

async function switchPortalTab(viewType, role) {
    window.currentView = viewType;

    // Update sidebar UI
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('onclick').includes(`'${viewType}'`)) {
            link.classList.add('active');
        }
    });

    // Update Section Title
    const titleHeader = document.querySelector('.main-content h1');
    if (titleHeader) {
        if (viewType === 'history') {
            titleHeader.innerText = 'Approval History';
        } else {
            const roleTitle = role.charAt(0).toUpperCase() + role.slice(1);
            titleHeader.innerText = `${roleTitle} Dashboard`;
        }
    }

    await renderRequests(role);
}

async function renderRequests(role) {
    const container = document.getElementById('requests-container');
    if (!container) return;

    const requests = await getRequests();
    const user = getCurrentUser();

    if (role === 'staff' && document.getElementById('staff-info')) {
        document.getElementById('staff-info').innerText = `${user.dept} | Year ${user.year} / Sec ${user.section} Advisor`;
    } else if (role === 'hod' && document.getElementById('hod-info')) {
        document.getElementById('hod-info').innerText = `${user.dept} Department HOD`;
    }

    let filteredRequests = requests;
    if (window.currentView === 'history') {
        filteredRequests = requests.filter(r => r.status === 'Approved' || r.status.includes('Rejected'));
    } else {
        filteredRequests = requests.filter(r => r.status === 'Pending');
    }

    if (!Array.isArray(filteredRequests) || filteredRequests.length === 0) {
        container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 4rem; color: var(--text-muted);">
            <i class="fas fa-clipboard-list" style="font-size: 3rem; margin-bottom: 1.5rem; opacity: 0.2;"></i>
            <p style="font-size: 1.1rem;">No ${window.currentView} requests found.</p>
        </div>`;
        return;
    }

    container.innerHTML = filteredRequests.map(req => {
        const leaveCount = req.leave_count || 0;
        const odCount = req.od_count || 0;
        const statusClass = getStatusClass(req.status);

        return `
        <div class="request-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
                <div style="display: flex; gap: 0.75rem; align-items: center;">
                    ${req.student?.photo ? `<img src="${req.student.photo}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover; border: 1px solid var(--border-main);">` : `<div style="width: 44px; height: 44px; border-radius: 8px; background: var(--bg-dark); display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-main);"><i class="fas fa-user-graduate" style="color: var(--text-dim);"></i></div>`}
                    <div>
                        <h4 style="color: var(--text-main); margin: 0; font-size: 1rem; font-weight: 700;">${req.student_name}</h4>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin: 0;">${req.dept} | ${req.year_sem_sec}</p>
                    </div>
                </div>
                <span class="status-badge ${statusClass}">${req.status.toUpperCase()}</span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.25rem;">
                <div style="background: var(--bg-dark); padding: 0.625rem; border-radius: 8px; border: 1px solid var(--border-light); text-align: center;">
                    <p style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 2px;">Past Leaves</p>
                    <p style="font-size: 1rem; font-weight: 700; color: var(--text-main); margin: 0;">${leaveCount}</p>
                </div>
                <div style="background: var(--bg-dark); padding: 0.625rem; border-radius: 8px; border: 1px solid var(--border-light); text-align: center;">
                    <p style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 2px;">Past ODs</p>
                    <p style="font-size: 1rem; font-weight: 700; color: var(--text-main); margin: 0;">${odCount}</p>
                </div>
            </div>

            <div style="padding: 1rem; border: 1px solid var(--border-light); border-radius: 8px; font-size: 0.875rem; margin-bottom: 1.25rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; color: var(--text-muted);">
                    <div><span style="display: block; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Type</span><strong style="color: var(--text-main)">${req.type}</strong></div>
                    <div><span style="display: block; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Resident</span><strong style="color: var(--text-main)">${req.resident_type}</strong></div>
                    <div><span style="display: block; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Duration</span><strong style="color: var(--primary)">${req.days} Day(s)</strong></div>
                    <div><span style="display: block; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Dates</span><strong style="color: var(--text-main)">${req.from_date}</strong></div>
                </div>
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-light);">
                    <span style="display: block; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">Reason</span>
                    <p style="color: var(--text-main); margin: 0; line-height: 1.4; font-size: 0.85rem;">${req.reason}</p>
                </div>
            </div>

            ${req.document ? `<div style="border-radius: 8px; overflow: hidden; border: 1px solid var(--border-light); cursor: pointer; margin-bottom: 1.25rem;" onclick="window.open('${req.document}')">
                <img src="${req.document}" style="width: 100%; height: 100px; object-fit: cover;">
            </div>` : ''}
            
            ${window.currentView === 'pending' ? `
            <div style="display: flex; gap: 0.75rem;">
                <button class="approve-btn" onclick="updateRequestStatus('${req._id?.$oid || req._id || req.id}', '${role}', 'approve')">
                    <i class="fas fa-check"></i> APPROVE
                </button>
                <button class="reject-btn" onclick="updateRequestStatus('${req._id?.$oid || req._id || req.id}', '${role}', 'reject')">
                    REJECT
                </button>
            </div>
            ` : `
            <div style="display: flex; gap: 0.75rem;">
                <button class="btn-primary" style="width: 100%;" onclick="printPass('${req._id?.$oid || req._id || req.id}')">
                    <i class="fas fa-eye"></i> WATCH DETAILS
                </button>
            </div>
            `}
        </div>
    `}).join('');
}

function renderAuthNav() {
    const nav = document.getElementById('auth-nav');
    if (!nav) return;
    const user = getCurrentUser();

    if (user) {
        nav.innerHTML = `
            <div style="display:flex; align-items:center; gap:1.5rem">
                <span style="font-size:0.9rem; color:var(--text-muted)">Welcome, <strong>${user.name}</strong></span>
                <button onclick="logout()" style="background:var(--secondary); border:none; color:white; padding: 0.4rem 1.25rem; border-radius: 0.75rem; cursor:pointer;">Logout</button>
            </div>
        `;
    }
}

async function autoFillStudentDetails(existingRequests = null) {
    const user = getCurrentUser();
    if (!user || user.role !== 'student') return;

    document.getElementById('student-name').value = user.name || '';
    document.getElementById('student-dept').value = user.dept || '';
    document.getElementById('student-year').value = user.year || '';
    document.getElementById('student-semester').value = user.semester || '';
    document.getElementById('student-section').value = user.section || '';

    // Use provided requests or fetch new ones
    const requests = existingRequests || await getRequests();
    if (!Array.isArray(requests)) return;

    const approved = requests.filter(r => r.status === 'Approved');
    document.getElementById('leave-count').innerText = approved.filter(r => r.type === 'Leave').length;
    document.getElementById('od-count').innerText = approved.filter(r => r.type === 'On Duty').length;
}

// Gate Management
async function recordGateEntry(data) {
    return await apiRequest('/gate/record', 'POST', data);
}

async function getGateHistory() {
    return await apiRequest('/gate/history');
}

async function clearGateHistory() {
    if (confirm("Clear all records?")) {
        await apiRequest('/gate/history/clear', 'POST');
        window.location.reload();
    }
}

function downloadGateHistoryCSV() {
    getGateHistory().then(history => {
        if (!Array.isArray(history) || history.length === 0) {
            alert("No records to download.");
            return;
        }

        const headers = ['Student Name', 'Department', 'Year/Section', 'Outing Time'];
        const rows = history.map(row => [
            `"${row.name}"`, `"${row.dept}"`, `"${row.year_sem_sec}"`, `"${row.outing_time}"`
        ]);

        const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `gate_records_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
}

function downloadGateHistoryPDF() {
    getGateHistory().then(history => {
        if (!Array.isArray(history) || history.length === 0) {
            alert("No records to generate PDF.");
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Add Header
        doc.setFontSize(18);
        doc.setTextColor(40);
        doc.text("Gate Exit Records - Smart Gate Pass", 14, 22);

        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);

        const tableColumn = ["#", "Student Name", "Department", "Year/Section", "Outing Time"];
        const tableRows = history.map((row, index) => [
            index + 1,
            row.name,
            row.dept,
            row.year_sem_sec,
            row.outing_time
        ]);

        doc.autoTable({
            head: [tableColumn],
            body: tableRows,
            startY: 40,
            theme: 'striped',
            headStyles: { fillColor: [59, 130, 246] }, // Institutional Blue
            styles: { fontSize: 9 }
        });

        doc.save(`gate_records_${new Date().toISOString().split('T')[0]}.pdf`);
    });
}

// Admin Logic
async function adminGetManagedUsers() {
    return await apiRequest('/admin/users');
}

async function adminDeleteUser(email) {
    return await apiRequest(`/admin/users/${email}`, 'DELETE');
}

async function adminUpdateUser(email, role, updatedData) {
    // Only send relevant fields based on role to maintain data integrity
    const payload = { name: updatedData.name };

    if (role !== 'warden') payload.dept = updatedData.dept;
    if (['staff', 'warden', 'student'].includes(role)) payload.year = updatedData.year;
    if (role === 'student') payload.semester = updatedData.semester;
    if (['staff', 'student'].includes(role)) payload.section = updatedData.section;
    if (role === 'student') payload.parent_mobile = updatedData.parent_mobile;

    return await apiRequest(`/admin/users/${email}`, 'PUT', payload);
}

// Holiday Management Logic
async function getHolidays() {
    return await apiRequest('/holidays');
}

async function handleHolidaySubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    const result = await apiRequest('/holidays', 'POST', data);
    if (result.success) {
        e.target.reset();
        renderHolidays();
    } else {
        alert(result.message);
    }
}

async function deleteHoliday(id) {
    if (!confirm('Remove this holiday from the calendar?')) return;
    const result = await apiRequest(`/holidays/${id}`, 'DELETE');
    if (result.success) {
        renderHolidays();
    } else {
        alert(result.message);
    }
}

async function renderHolidays() {
    const container = document.getElementById('holidays-list-container');
    if (!container) return;

    const holidays = await getHolidays();
    if (!Array.isArray(holidays) || holidays.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No holidays scheduled.</p>';
        return;
    }

    container.innerHTML = holidays.map(h => `
        <div style="background: var(--glass-highlight); padding: 1rem; border-radius: 0.75rem; border: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="margin: 0; font-weight: bold; color: var(--primary);">${h.date}</p>
                <p style="margin: 0; font-size: 0.85rem; color: var(--text-main);">${h.reason}</p>
            </div>
            <button onclick="deleteHoliday('${h._id.$oid || h._id}')" style="background: transparent; border: none; color: #ff4444; cursor: pointer; padding: 0.5rem;">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}



