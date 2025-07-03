# backend/app/routes/document_review.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os

review_bp = Blueprint('review', __name__, url_prefix='/admin')

def require_admin():
    """Función auxiliar para verificar permisos de admin"""
    return session.get('user_role') == 'admin'

@review_bp.route('/documents')
def review_documents():
    """Panel principal de revisión de documentos"""
    if not require_admin():
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('login'))
    
    # Simular base de datos de documentos para revisión
    # En producción esto vendría de MongoDB
    all_documents = []
    
    # Obtener documentos de todas las sesiones de usuarios
    # Por ahora simularemos con algunos documentos de ejemplo
    sample_documents = [
        {
            'id': 'doc_001',
            'user_email': 'proveedor1@empresa.com',
            'company_name': 'Empresa Proveedor S.A.S',
            'document_type': 'acuerdo_seguridad',
            'document_name': 'Acuerdo de Seguridad Proveedores',
            'filename': 'acuerdo_seguridad_123456789_20250102.txt',
            'created_at': '2025-01-02T10:30:00',
            'status': 'pending',
            'priority': 'high',
            'file_size': '25 KB'
        },
        {
            'id': 'doc_002',
            'user_email': 'proveedor2@empresa.com',
            'company_name': 'Flores del Valle Ltda',
            'document_type': 'autorizacion_datos',
            'document_name': 'Autorización de Tratamiento de Datos',
            'filename': 'autorizacion_datos_987654321_20250102.txt',
            'created_at': '2025-01-02T14:15:00',
            'status': 'in_review',
            'priority': 'medium',
            'file_size': '18 KB',
            'reviewer': 'admin@montanel.com',
            'review_started': '2025-01-02T15:00:00'
        }
    ]
    
    # Agregar documentos reales de la sesión si existen
    for user_email, user_data in session.get('all_users', {}).items():
        if user_email != session.get('user_email'):  # No incluir al admin actual
            user_docs = session.get(f'docs_{user_email}', [])
            for doc in user_docs:
                all_documents.append({
                    'id': f"real_{len(all_documents)}",
                    'user_email': user_email,
                    'company_name': user_data.get('profile', {}).get('company_name', 'Sin nombre'),
                    'document_type': doc.get('form_type'),
                    'document_name': doc.get('form_type', '').replace('_', ' ').title(),
                    'filename': doc.get('filename'),
                    'created_at': doc.get('created_at'),
                    'status': doc.get('status', 'pending'),
                    'priority': 'medium',
                    'file_size': '20 KB'
                })
    
    # Combinar con documentos de ejemplo
    all_documents.extend(sample_documents)
    
    # Estadísticas
    pending_count = len([d for d in all_documents if d['status'] == 'pending'])
    in_review_count = len([d for d in all_documents if d['status'] == 'in_review'])
    approved_count = len([d for d in all_documents if d['status'] == 'approved'])
    rejected_count = len([d for d in all_documents if d['status'] == 'rejected'])
    
    return render_template('admin/document_review.html',
                         documents=all_documents,
                         pending_count=pending_count,
                         in_review_count=in_review_count,
                         approved_count=approved_count,
                         rejected_count=rejected_count)

@review_bp.route('/documents/<doc_id>')
def review_document_detail(doc_id):
    """Vista detallada de un documento para revisión"""
    if not require_admin():
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('login'))
    
    # Buscar el documento (simulado)
    document = {
        'id': doc_id,
        'user_email': 'proveedor1@empresa.com',
        'company_name': 'Empresa Proveedor S.A.S',
        'document_type': 'acuerdo_seguridad',
        'document_name': 'Acuerdo de Seguridad Proveedores',
        'filename': 'acuerdo_seguridad_123456789_20250102.txt',
        'created_at': '2025-01-02T10:30:00',
        'status': 'pending',
        'priority': 'high',
        'file_size': '25 KB',
        'form_data': {
            'razon_social': 'Empresa Proveedor S.A.S',
            'nit': '123456789-0',
            'representante_legal': 'Juan Pérez García',
            'direccion': 'Calle 123 #45-67',
            'telefono': '601-2345678',
            'email': 'contacto@empresaproveedor.com'
        }
    }
    
    return render_template('admin/document_detail.html', document=document)

@review_bp.route('/documents/<doc_id>/update-status', methods=['POST'])
def update_document_status(doc_id):
    """Actualizar estado de un documento"""
    if not require_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    comments = data.get('comments', '')
    
    # Validar estados permitidos
    allowed_statuses = ['pending', 'in_review', 'approved', 'rejected']
    if new_status not in allowed_statuses:
        return jsonify({'error': 'Estado no válido'}), 400
    
    # Aquí actualizarías en la base de datos real
    # Por ahora simulamos la actualización
    
    # Registrar la acción
    review_action = {
        'document_id': doc_id,
        'reviewer': session.get('user_email'),
        'action': new_status,
        'comments': comments,
        'timestamp': datetime.now().isoformat()
    }
    
    # Guardar en sesión (simulado)
    if 'review_actions' not in session:
        session['review_actions'] = []
    session['review_actions'].append(review_action)
    session.modified = True
    
    flash(f'Documento {new_status.replace("_", " ")} exitosamente', 'success')
    
    return jsonify({
        'success': True,
        'message': f'Estado actualizado a {new_status}',
        'new_status': new_status
    })

@review_bp.route('/documents/<doc_id>/download')
def download_document_for_review(doc_id):
    """Descargar documento para revisión"""
    if not require_admin():
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('login'))
    
    # Aquí iría la lógica para encontrar y servir el archivo
    # Por ahora redirigimos a la función de descarga normal
    return redirect(url_for('download_document', filename='ejemplo.txt'))

@review_bp.route('/documents/bulk-action', methods=['POST'])
def bulk_document_action():
    """Acciones en lote para múltiples documentos"""
    if not require_admin():
        return jsonify({'error': 'Acceso denegado'}), 403
    
    data = request.get_json()
    document_ids = data.get('document_ids', [])
    action = data.get('action')
    
    if not document_ids or not action:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Procesar acción en lote
    success_count = 0
    for doc_id in document_ids:
        # Aquí iría la lógica de actualización real
        success_count += 1
    
    return jsonify({
        'success': True,
        'message': f'{action} aplicado a {success_count} documentos',
        'processed_count': success_count
    })

@review_bp.route('/analytics')
def review_analytics():
    """Panel de análisis y métricas de revisión"""
    if not require_admin():
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('login'))
    
    # Datos de ejemplo para análisis
    analytics_data = {
        'daily_submissions': [
            {'date': '2025-01-01', 'count': 5},
            {'date': '2025-01-02', 'count': 8},
            {'date': '2025-01-03', 'count': 3},
        ],
        'document_types': {
            'acuerdo_seguridad': 12,
            'autorizacion_datos': 10,
            'formulario_vinculacion': 5
        },
        'average_review_time': '2.5 días',
        'approval_rate': '85%'
    }
    
    return render_template('admin/review_analytics.html', data=analytics_data)