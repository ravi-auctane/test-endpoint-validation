"""
Example API file to test endpoint validation
This file contains both valid and invalid endpoints
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# ✅ VALID ENDPOINTS - These follow allowed parent paths

@app.route('/api/v1/users')
def get_users():
    """Valid: follows /api/v1 parent path"""
    return jsonify({"users": []})

@app.route('/api/v1/users/<int:user_id>')
def get_user(user_id):
    """Valid: follows /api/v1 parent path with parameter"""
    return jsonify({"user_id": user_id})

@app.route('/api/v2/products')
def get_products():
    """Valid: follows /api/v2 parent path"""
    return jsonify({"products": []})

@app.route('/api/v2/admin/dashboard')
def admin_dashboard():
    """Valid: follows /admin parent path"""
    return jsonify({"status": "admin"})

@app.route('/api/v1/public/about')
def public_about():
    """Valid: follows /public parent path"""
    return jsonify({"page": "about"})

@app.route('/api/v2/auth/login', methods=['POST'])
def login():
    """Valid: follows /auth parent path"""
    return jsonify({"token": "xxx"})

@app.route('/api/v4/health/status')
def health_check():
    """Valid: follows /health parent path"""
    return jsonify({"status": "healthy"})

# ❌ INVALID ENDPOINTS - These will fail validation

@app.route('/api/v1/users/users/profile')  # Missing /api/v1 or /api/v2 prefix
def user_profile():
    """Invalid: doesn't follow any allowed parent path"""
    return jsonify({"profile": {}})

@app.route('/api/v1/users/test/endpoint')  # /test is not an allowed parent path
def test_endpoint():
    """Invalid: test endpoints should not exist in production"""
    return jsonify({"test": True})

@app.route('/api/v1/users/debug/logs')  # /debug is not allowed
def debug_logs():
    """Invalid: debug endpoints should not exist in production"""
    return jsonify({"logs": []})

@app.route('/api/v2/users/temp/data')  # /temp is not allowed
def temp_data():
    """Invalid: temporary endpoints should not exist"""
    return jsonify({"temp": []})

@app.route('/api/v2/users/random/path/to/endpoint')  # Completely non-standard path
def random_endpoint():
    """Invalid: doesn't follow any convention"""
    return jsonify({"random": True})

# ✅ VALID ENDPOINTS - More examples

@app.route('/api/v1/orders', methods=['GET', 'POST'])
def orders():
    """Valid: REST endpoint following /api/v1"""
    if request.method == 'POST':
        return jsonify({"created": True})
    return jsonify({"orders": []})

@app.route('/api/v1/orders/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
def order_detail(order_id):
    """Valid: RESTful resource endpoint"""
    if request.method == 'DELETE':
        return jsonify({"deleted": order_id})
    elif request.method == 'PUT':
        return jsonify({"updated": order_id})
    return jsonify({"order_id": order_id})

if __name__ == '__main__':
    app.run(debug=False)  # Never use debug=True in production
