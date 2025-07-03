# backend/app/routes/clients.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from datetime import datetime, timedelta
import json

client_bp = Blueprint('client', __name__, url_prefix='/client')

def require_login():
    """Función auxiliar para verificar login"""
    if not session.get('user_email'):
        flash('Debes iniciar sesión para acceder', 'error')
        return False
    return True

def require_client():
    """Función auxiliar para verificar rol de cliente"""
    if not require_login():
        return False
    if session.get('user_role') not in ['client', 'admin']:
        flash('Acceso denegado', 'error')
        return False
    return True

@client_bp.route('/dashboard')
def dashboard():
    if not require_client():
        return redirect(url_for('auth.login'))
    
    user_email = session.get('user_email')
    
    # Obtener datos del usuario
    from app.routes.auth import get_users_db
    users_db = get_users_db()
    user = users_db.get(user_email)
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('auth.login'))
    
    # Simular datos de proveedores asociados
    providers = [
        {
            'id': 1,
            'company_name': 'Proveedor Flores A',
            'nit': '123456789-0',
            'status': 'active',
            'documents_completed': 2,
            'documents_total': 3,
            'last_update': datetime.now() - timedelta(days=2)
        },
        {
            'id': 2,
            'company_name': 'Proveedor Flores B',
            'nit': '987654321-0',
            'status': 'pending',
            'documents_completed': 1,
            'documents_total': 3,
            'last_update': datetime.now() - timedelta(days=5)
        },
        {
            'id': 3,
            'company_name': 'Proveedor Insumos C',
            'nit': '456789123-0',
            'status': 'active',
            'documents_completed': 3,
            'documents_total': 3,
            'last_update': datetime.now() - timedelta(days=1)
        }
    ]
    
    # Calcular estadísticas
    total_providers = len(providers)
    active_providers = len([p for p in providers if p['status'] == 'active'])
    pending_providers = len([p for p in providers if p['status'] == 'pending'])
    total_documents = sum(p['documents_total'] for p in providers)
    completed_documents = sum(p['documents_completed'] for p in providers)
    
    stats = {
        'total_providers': total_providers,
        'active_providers': active_providers,
        'pending_providers': pending_providers,
        'total_documents': total_documents,
        'completed_documents': completed_documents,
        'completion_rate': round((completed_documents / total_documents * 100) if total_documents > 0 else 0, 1)
    }
    
    return render_template('client/dashboard.html', 
                         user=user,
                         providers=providers,
                         stats=stats)

@client_bp.route('/providers')
def providers():
    if not require_client():
        return redirect(url_for('auth.login'))
    
    # Simular lista completa de proveedores
    providers = [
        {
            'id': 1,
            'company_name': 'Proveedor Flores A',
            'nit': '123456789-0',
            'contact_email': 'contacto@proveedora.com',
            'phone': '601-2345678',
            'status': 'active',
            'documents_completed': 2,
            'documents_total': 3,
            'last_update': datetime.now() - timedelta(days=2),
            'compliance_score': 85
        },
        {
            'id': 2,
            'company_name': 'Proveedor Flores B',
            'nit': '987654321-0',
            'contact_email': 'info@proveedorb.com',
            'phone': '601-8765432',
            'status': 'pending',
            'documents_completed': 1,
            'documents_total': 3,
            'last_update': datetime.now() - timedelta(days=5),
            'compliance_score': 45
        },
        {
            'id': 3,
            'company_name': 'Proveedor Insumos C',
            'nit': '456789123-0',
            'contact_email': 'ventas@insumosC.com',
            'phone': '601-3456789',
            'status': 'active',
            'documents_completed': 3,
            'documents_total': 3,
            'last_update': datetime.now() - timedelta(days=1),
            'compliance_score': 100
        }
    ]
    
    return render_template('client/providers.html', providers=providers)

@client_bp.route('/providers/<int:provider_id>')
def provider_detail(provider_id):
    if not require_client():
        return redirect(url_for('auth.login'))
    
    # Simular datos detallados del proveedor
    provider = {
        'id': provider_id,
        'company_name': 'Proveedor Flores A',
        'nit': '123456789-0',
        'contact_email': 'contacto@proveedora.com',
        'phone': '601-2345678',
        'address': 'Calle 123 #45-67, Bogotá',
        'legal_representative': 'Juan Pérez García',
        'status': 'active',
        'registration_date': datetime.now() - timedelta(days=30),
        'compliance_score': 85
    }
    
    # Simular documentos del proveedor
    documents = [
        {
            'id': 1,
            'name': 'Acuerdo de Seguridad',
            'type': 'acuerdo_seguridad',
            'status': 'approved',
            'upload_date': datetime.now() - timedelta(days=20),
            'approval_date': datetime.now() - timedelta(days=18),
            'expiry_date': datetime.now() + timedelta(days=345)
        },
        {
            'id': 2,
            'name': 'Autorización de Datos',
            'type': 'autorizacion_datos',
            'status': 'approved',
            'upload_date': datetime.now() - timedelta(days=15),
            'approval_date': datetime.now() - timedelta(days=13),
            'expiry_date': datetime.now() + timedelta(days=350)
        },
        {
            'id': 3,
            'name': 'Formulario de Vinculación',
            'type': 'formulario_vinculacion',
            'status': 'pending',
            'upload_date': None,
            'approval_date': None,
            'expiry_date': None
        }
    ]
    
    return render_template('client/provider_detail.html', 
                         provider=provider, 
                         documents=documents)

@client_bp.route('/documents')
def documents():
    if not require_client():
        return redirect(url_for('auth.login'))
    
    # Simular todos los documentos de todos los proveedores
    all_documents = [
        {
            'id': 1,
            'provider_name': 'Proveedor Flores A',
            'provider_nit': '123456789-0',
            'document_name': 'Acuerdo de Seguridad',
            'document_type': 'acuerdo_seguridad',
            'status': 'approved',
            'upload_date': datetime.now() - timedelta(days=20),
            'approval_date': datetime.now() - timedelta(days=18)
        },
        {
            'id': 2,
            'provider_name': 'Proveedor Flores A',
            'provider_nit': '123456789-0',
            'document_name': 'Autorización de Datos',
            'document_type': 'autorizacion_datos',
            'status': 'approved',
            'upload_date': datetime.now() - timedelta(days=15),
            'approval_date': datetime.now() - timedelta(days=13)
        },
        {
            'id': 3,
            'provider_name': 'Proveedor Flores B',
            'provider_nit': '987654321-0',
            'document_name': 'Acuerdo de Seguridad',
            'document_type': 'acuerdo_seguridad',
            'status': 'pending',
            'upload_date': datetime.now() - timedelta(days=5),
            'approval_date': None
        }
    ]
    
    return render_template('client/documents.html', documents=all_documents)

@client_bp.route('/reports')
def reports():
    if not require_client():
        return redirect(url_for('auth.login'))
    
    # Simular datos para reportes
    monthly_stats = [
        {'month': 'Enero', 'new_providers': 5, 'documents_processed': 15, 'completion_rate': 85},
        {'month': 'Febrero', 'new_providers': 3, 'documents_processed': 12, 'completion_rate': 90},
        {'month': 'Marzo', 'new_providers': 7, 'documents_processed': 21, 'completion_rate': 88}
    ]
    
    compliance_by_type = [
        {'document_type': 'Acuerdo de Seguridad', 'total': 15, 'approved': 13, 'pending': 2},
        {'document_type': 'Autorización de Datos', 'total': 15, 'approved': 12, 'pending': 3},
        {'document_type': 'Formulario de Vinculación', 'total': 15, 'approved': 8, 'pending': 7}
    ]
    
    return render_template('client/reports.html', 
                         monthly_stats=monthly_stats,
                         compliance_by_type=compliance_by_type)

@client_bp.route('/notifications')
def notifications():
    if not require_client():
        return redirect(url_for('auth.login'))
    
    # Simular notificaciones para clientes
    notifications = [
        {
            'id': 1,
            'title': 'Nuevo Proveedor Registrado',
            'message': 'Proveedor Flores D se ha registrado y requiere aprobación',
            'type': 'info',
            'date': datetime.now() - timedelta(hours=2),
            'read': False,
            'action_url': '/client/providers/4'
        },
        {
            'id': 2,
            'title': 'Documento Vencido',
            'message': 'El Acuerdo de Seguridad de Proveedor B vencerá en 30 días',
            'type': 'warning',
            'date': datetime.now() - timedelta(days=1),
            'read': True,
            'action_url': '/client/providers/2'
        },
        {
            'id': 3,
            'title': 'Reporte Mensual Disponible',
            'message': 'El reporte de cumplimiento de marzo está listo',
            'type': 'success',
            'date': datetime.now() - timedelta(days=3),
            'read': True,
            'action_url': '/client/reports'
        }
    ]
    
    return render_template('client/notifications.html', notifications=notifications)

@client_bp.route('/settings')
def settings():
    if not require_client():
        return redirect(url_for('auth.login'))
    
    from app.routes.auth import get_users_db
    users_db = get_users_db()
    user = users_db.get(session['user_email'])
    
    return render_template('client/settings.html', user=user)

@client_bp.route('/providers/<int:provider_id>/approve', methods=['POST'])
def approve_provider(provider_id):
    if not require_client():
        return redirect(url_for('auth.login'))
    
    # Aquí iría la lógica para aprobar un proveedor
    flash(f'Proveedor {provider_id} aprobado exitosamente', 'success')
    return redirect(url_for('client.providers'))

@client_bp.route('/providers/<int:provider_id>/reject', methods=['POST'])
def reject_provider(provider_id):
    if not require_client():
        return redirect(url_for('auth.login'))
    
    reason = request.form.get('reason', 'Sin razón especificada')
    
    # Aquí iría la lógica para rechazar un proveedor
    flash(f'Proveedor {provider_id} rechazado: {reason}', 'warning')
    return redirect(url_for('client.providers'))