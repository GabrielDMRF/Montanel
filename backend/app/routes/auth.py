# backend/app/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

auth_bp = Blueprint('auth', __name__)

# Simulación de base de datos (temporal)
users_db = {
    'admin@montanel.com': {
        'password': generate_password_hash('admin123'),
        'role': 'admin',
        'profile': {
            'company_name': 'Inversiones Montanel SAS',
            'nit': '860.009.240-2',
            'legal_representative': 'Laura Arboleda Calderon'
        },
        'created_at': datetime.now()
    }
}

def get_users_db():
    """Función para obtener la base de datos de usuarios"""
    return users_db

def require_login():
    """Función auxiliar para verificar login"""
    if not session.get('user_email'):
        return False
    return True

def require_role(role):
    """Función auxiliar para verificar roles"""
    if not require_login():
        return False
    return session.get('user_role') == role

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Por favor complete todos los campos', 'error')
            return render_template('auth/login.html')
        
        user = users_db.get(email)
        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            session['user_role'] = user['role']
            session['user_profile'] = user.get('profile', {})
            
            flash('Inicio de sesión exitoso', 'success')
            
            # Redirigir según el rol
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'client':
                return redirect(url_for('client_dashboard'))
            else:
                return redirect(url_for('provider_dashboard'))
        else:
            flash('Credenciales inválidas', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Recopilar datos del formulario
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'provider')
        company_name = request.form.get('company_name')
        nit = request.form.get('nit')
        legal_representative = request.form.get('legal_representative')
        
        # Validaciones básicas
        if not all([email, password, company_name, nit, legal_representative]):
            flash('Por favor complete todos los campos obligatorios', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('auth/register.html')
        
        if email in users_db:
            flash('El email ya está registrado', 'error')
            return render_template('auth/register.html')
        
        # Crear nuevo usuario
        try:
            users_db[email] = {
                'password': generate_password_hash(password),
                'role': role,
                'profile': {
                    'company_name': company_name,
                    'nit': nit,
                    'legal_representative': legal_representative
                },
                'created_at': datetime.now(),
                'status': 'active'
            }
            
            flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Error al crear la cuenta: {str(e)}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
def profile():
    if not require_login():
        flash('Debes iniciar sesión para acceder', 'error')
        return redirect(url_for('auth.login'))
    
    user = users_db.get(session['user_email'])
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if not require_login():
        flash('Debes iniciar sesión para acceder', 'error')
        return redirect(url_for('auth.login'))
    
    user_email = session['user_email']
    user = users_db.get(user_email)
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Actualizar perfil
        user['profile'].update({
            'company_name': request.form.get('company_name', ''),
            'nit': request.form.get('nit', ''),
            'legal_representative': request.form.get('legal_representative', '')
        })
        
        # Actualizar sesión
        session['user_profile'] = user['profile']
        
        flash('Perfil actualizado correctamente', 'success')
        
    except Exception as e:
        flash(f'Error al actualizar perfil: {str(e)}', 'error')
    
    return redirect(url_for('auth.profile'))

# Función para usar en templates
@auth_bp.app_context_processor
def inject_user():
    current_user = None
    if session.get('user_email'):
        current_user = users_db.get(session['user_email'])
    return dict(current_user=current_user)