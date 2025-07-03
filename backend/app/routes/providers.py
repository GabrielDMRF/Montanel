# backend/app/routes/providers.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, send_file
from datetime import datetime
import os

provider_bp = Blueprint('provider', __name__, url_prefix='/provider')

def require_login():
    """Función auxiliar para verificar login"""
    if not session.get('user_email'):
        flash('Debes iniciar sesión para acceder', 'error')
        return False
    return True

def require_provider():
    """Función auxiliar para verificar rol de proveedor"""
    if not require_login():
        return False
    if session.get('user_role') not in ['provider', 'admin']:
        flash('Acceso denegado', 'error')
        return False
    return True

@provider_bp.route('/dashboard')
def dashboard():
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    user_email = session.get('user_email')
    
    # Simular datos del usuario (en producción vendría de BD)
    from app.routes.auth import get_users_db
    users_db = get_users_db()
    user = users_db.get(user_email)
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('auth.login'))
    
    # Obtener documentos del usuario
    documents = session.get('form_submissions', [])
    completed_docs = len([doc for doc in documents if doc.get('status') == 'completed'])
    
    return render_template('provider/dashboard.html', 
                         user=user,
                         documents=documents,
                         completed_docs=completed_docs)

@provider_bp.route('/documents')
def documents():
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    documents = session.get('form_submissions', [])
    
    return render_template('provider/documents.html', documents=documents)

@provider_bp.route('/documents/upload', methods=['GET', 'POST'])
def upload_document():
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Aquí iría la lógica de upload de archivos
        flash('Funcionalidad de upload en desarrollo', 'info')
        return redirect(url_for('provider.documents'))
    
    return render_template('provider/upload.html')

@provider_bp.route('/profile')
def profile():
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    from app.routes.auth import get_users_db
    users_db = get_users_db()
    user = users_db.get(session['user_email'])
    
    return render_template('provider/profile.html', user=user)

@provider_bp.route('/help')
def help():
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    return render_template('provider/help.html')

@provider_bp.route('/notifications')
def notifications():
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    # Simular notificaciones
    notifications = [
        {
            'id': 1,
            'title': 'Documento Aprobado',
            'message': 'Su Acuerdo de Seguridad ha sido aprobado',
            'type': 'success',
            'date': datetime.now(),
            'read': False
        },
        {
            'id': 2,
            'title': 'Recordatorio',
            'message': 'Complete el formulario de Autorización de Datos',
            'type': 'warning',
            'date': datetime.now(),
            'read': True
        }
    ]
    
    return render_template('provider/notifications.html', notifications=notifications)

@provider_bp.route('/documents/status/<doc_id>')
def document_status(doc_id):
    if not require_provider():
        return redirect(url_for('auth.login'))
    
    # Buscar documento por ID
    documents = session.get('form_submissions', [])
    document = None
    
    for doc in documents:
        if str(doc.get('id', '')) == doc_id or doc.get('filename', '').startswith(doc_id):
            document = doc
            break
    
    if not document:
        flash('Documento no encontrado', 'error')
        return redirect(url_for('provider.documents'))
    
    # Simular historial de estados
    status_history = [
        {
            'status': 'submitted',
            'date': datetime.now(),
            'description': 'Documento enviado para revisión'
        },
        {
            'status': 'in_review',
            'date': datetime.now(),
            'description': 'Documento en proceso de revisión'
        }
    ]
    
    return render_template('provider/document_status.html', 
                         document=document, 
                         status_history=status_history)

# Función para usar en otros módulos
def get_provider_dashboard_data(user_email):
    """Obtiene datos del dashboard del proveedor"""
    documents = session.get('form_submissions', [])
    
    return {
        'total_documents': len(documents),
        'completed_documents': len([d for d in documents if d.get('status') == 'completed']),
        'pending_documents': len([d for d in documents if d.get('status') == 'pending']),
        'approved_documents': len([d for d in documents if d.get('status') == 'approved']),
        'rejected_documents': len([d for d in documents if d.get('status') == 'rejected'])
    }