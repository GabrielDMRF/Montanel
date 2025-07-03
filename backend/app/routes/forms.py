# backend/app/routes/forms.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import os
import sys

# Agregar el directorio padre al path para importar servicios
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

forms_bp = Blueprint('forms', __name__, url_prefix='/forms')

def require_login():
    """Función auxiliar para verificar login"""
    if not session.get('user_email'):
        flash('Debes iniciar sesión para acceder', 'error')
        return False
    return True

@forms_bp.route('/acuerdo-seguridad', methods=['GET', 'POST'])
def acuerdo_seguridad():
    if not require_login():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Importar el generador de documentos
            from app.services.document_generator import DocumentGenerator
            
            # Recopilar datos del formulario
            form_data = {
                'razon_social': request.form.get('razon_social'),
                'nit': request.form.get('nit'),
                'representante_legal': request.form.get('representante_legal'),
                'cedula_representante': request.form.get('cedula_representante'),
                'direccion': request.form.get('direccion'),
                'telefono': request.form.get('telefono'),
                'email': request.form.get('email')
            }
            
            # Validar campos requeridos
            required_fields = ['razon_social', 'nit', 'representante_legal', 'direccion', 'telefono']
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                flash(f'Faltan campos requeridos: {", ".join(missing_fields)}', 'error')
                return render_template('provider/forms/acuerdo_seguridad.html', form_data=form_data)
            
            # Generar documento
            generator = DocumentGenerator()
            user_data = {'email': session.get('user_email')}
            
            filepath, filename = generator.generate_acuerdo_seguridad(form_data, user_data)
            
            # Guardar en "base de datos" (simulada)
            if 'form_submissions' not in session:
                session['form_submissions'] = []
            
            submission = {
                'form_type': 'acuerdo_seguridad',
                'form_data': form_data,
                'filename': filename,
                'filepath': filepath,
                'created_at': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            session['form_submissions'].append(submission)
            session.modified = True
            
            flash('¡Documento generado exitosamente! Puedes descargarlo desde tu dashboard.', 'success')
            return redirect(url_for('provider_dashboard'))
            
        except Exception as e:
            flash(f'Error al generar el documento: {str(e)}', 'error')
            return render_template('provider/forms/acuerdo_seguridad.html')
    
    return render_template('provider/forms/acuerdo_seguridad.html')

@forms_bp.route('/autorizacion-datos', methods=['GET', 'POST'])
def autorizacion_datos():
    if not require_login():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from app.services.document_generator import DocumentGenerator
            
            form_data = {
                'razon_social': request.form.get('razon_social'),
                'nit': request.form.get('nit'),
                'representante_legal': request.form.get('representante_legal'),
                'cedula_representante': request.form.get('cedula_representante'),
                'ciudad': request.form.get('ciudad'),
                'email': request.form.get('email')
            }
            
            # Validar campos requeridos
            required_fields = ['razon_social', 'nit', 'representante_legal', 'cedula_representante', 'ciudad']
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            
            if missing_fields:
                flash(f'Faltan campos requeridos: {", ".join(missing_fields)}', 'error')
                return render_template('provider/forms/autorizacion_datos.html', form_data=form_data)
            
            # Generar documento
            generator = DocumentGenerator()
            user_data = {'email': session.get('user_email')}
            
            filepath, filename = generator.generate_autorizacion_datos(form_data, user_data)
            
            # Guardar en "base de datos"
            if 'form_submissions' not in session:
                session['form_submissions'] = []
            
            submission = {
                'form_type': 'autorizacion_datos',
                'form_data': form_data,
                'filename': filename,
                'filepath': filepath,
                'created_at': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            session['form_submissions'].append(submission)
            session.modified = True
            
            flash('¡Documento generado exitosamente! Puedes descargarlo desde tu dashboard.', 'success')
            return redirect(url_for('provider_dashboard'))
            
        except Exception as e:
            flash(f'Error al generar el documento: {str(e)}', 'error')
            return render_template('provider/forms/autorizacion_datos.html')
    
    return render_template('provider/forms/autorizacion_datos.html')

@forms_bp.route('/download/<filename>')
def download_document(filename):
    """Ruta para descargar documentos generados"""
    if not require_login():
        return redirect(url_for('login'))
    
    try:
        # Verificar que el archivo pertenece al usuario actual
        user_submissions = session.get('form_submissions', [])
        file_found = False
        
        for submission in user_submissions:
            if submission.get('filename') == filename:
                file_found = True
                filepath = submission.get('filepath')
                break
        
        if not file_found:
            flash('Archivo no encontrado o sin permisos', 'error')
            return redirect(url_for('provider_dashboard'))
        
        if not os.path.exists(filepath):
            flash('El archivo no existe en el servidor', 'error')
            return redirect(url_for('provider_dashboard'))
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        flash(f'Error al descargar el archivo: {str(e)}', 'error')
        return redirect(url_for('provider_dashboard'))

@forms_bp.route('/preview/<form_type>')
def preview_form(form_type):
    """Vista previa del formulario antes de completar"""
    if not require_login():
        return redirect(url_for('login'))
    
    templates = {
        'acuerdo_seguridad': 'provider/forms/preview_acuerdo.html',
        'autorizacion_datos': 'provider/forms/preview_autorizacion.html'
    }
    
    template = templates.get(form_type)
    if not template:
        flash('Tipo de formulario no válido', 'error')
        return redirect(url_for('provider_dashboard'))
    
    return render_template(template, form_type=form_type)