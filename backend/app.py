# backend/app.py
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__, 
           template_folder='../frontend/templates',
           static_folder='../frontend/static')

# Configuraciones básicas
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu-clave-secreta-temporal-123')

# Base de datos simulada (temporal, luego usaremos MongoDB)
users_db = {
    'admin@montanel.com': {
        'password': generate_password_hash('admin123'),
        'role': 'admin',
        'profile': {
            'company_name': 'Inversiones Montanel SAS',
            'nit': '860.009.240-2',
            'legal_representative': 'Laura Arboleda Calderon'
        }
    }
}

# Importar servicios
try:
    from services.document_generator import DocumentGenerator
    document_generator = DocumentGenerator()
except ImportError:
    print("Advertencia: No se pudo importar DocumentGenerator. Creando carpetas necesarias...")
    os.makedirs('generated_documents', exist_ok=True)
    document_generator = None

# Función auxiliar para verificar login
def require_login():
    return session.get('user_email') is not None

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = users_db.get(email)
        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            session['user_role'] = user['role']
            
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

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('index'))

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'provider')
        
        if email in users_db:
            flash('El email ya está registrado', 'error')
        else:
            users_db[email] = {
                'password': generate_password_hash(password),
                'role': role,
                'profile': {
                    'company_name': request.form.get('company_name', ''),
                    'nit': request.form.get('nit', ''),
                    'legal_representative': request.form.get('legal_representative', '')
                },
                'created_at': datetime.now()
            }
            flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    
    return render_template('auth/register.html')

# Dashboards
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('user_email') or session.get('user_role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('login'))
    
    # Calcular estadísticas
    total_submissions = 0
    for user_email in users_db:
        user_submissions = session.get('form_submissions', []) if session.get('user_email') == user_email else []
        total_submissions += len(user_submissions)
    
    return render_template('admin/dashboard.html', 
                         total_users=len(users_db),
                         total_documents=total_submissions,
                         users=users_db)

@app.route('/client/dashboard')
def client_dashboard():
    if not session.get('user_email'):
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))
    
    user = users_db.get(session['user_email'])
    user_submissions = session.get('form_submissions', [])
    
    return render_template('client/dashboard.html', 
                         user=user,
                         documents=user_submissions)

@app.route('/provider/dashboard')
def provider_dashboard():
    if not session.get('user_email'):
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))
    
    user = users_db.get(session['user_email'])
    user_submissions = session.get('form_submissions', [])
    
    # Contar documentos por estado
    completed_docs = len([doc for doc in user_submissions if doc.get('status') == 'completed'])
    
    return render_template('provider/dashboard.html', 
                         user=user,
                         documents=user_submissions,
                         completed_docs=completed_docs)

# ===============================
# RUTAS DE FORMULARIOS
# ===============================

@app.route('/forms/acuerdo-seguridad', methods=['GET', 'POST'])
def acuerdo_seguridad():
    if not require_login():
        flash('Debes iniciar sesión para acceder', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
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
            
            # Generar archivo (intentar Word primero, si falla usar texto)
            try:
                # Intentar generar Word si python-docx está disponible
                from services.word_generator import generate_acuerdo_seguridad_word
                filepath = generate_acuerdo_seguridad_word(form_data)
                
                if filepath and os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                else:
                    raise Exception("Fallo generación Word")
                    
            except (ImportError, Exception):
                # Si falla Word, usar generación de texto
                filepath = generate_acuerdo_seguridad_file(form_data)
                
                if not filepath or not os.path.exists(filepath):
                    flash('Error al generar el documento', 'error')
                    return render_template('provider/forms/acuerdo_seguridad.html', form_data=form_data)
                
                filename = os.path.basename(filepath)
            
            # Guardar en "base de datos" de sesión
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

@app.route('/forms/autorizacion-datos', methods=['GET', 'POST'])
def autorizacion_datos():
    if not require_login():
        flash('Debes iniciar sesión para acceder', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
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
            
            # Generar archivo (intentar Word primero, si falla usar texto)
            try:
                # Intentar generar Word si python-docx está disponible
                from services.word_generator import generate_autorizacion_datos_word
                filepath = generate_autorizacion_datos_word(form_data)
                
                if filepath and os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                else:
                    raise Exception("Fallo generación Word")
                    
            except (ImportError, Exception):
                # Si falla Word, usar generación de texto
                filepath = generate_autorizacion_datos_file(form_data)
                
                if not filepath or not os.path.exists(filepath):
                    flash('Error al generar el documento', 'error')
                    return render_template('provider/forms/autorizacion_datos.html', form_data=form_data)
                
                filename = os.path.basename(filepath)
            
            # Guardar en sesión
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
            
            flash('¡Documento generado exitosamente!', 'success')
            return redirect(url_for('provider_dashboard'))
            
        except Exception as e:
            flash(f'Error al generar el documento: {str(e)}', 'error')
    
    return render_template('provider/forms/autorizacion_datos.html')

@app.route('/download/<filename>')
def download_document(filename):
    """Ruta para descargar documentos generados"""
    if not require_login():
        flash('Debes iniciar sesión para acceder', 'error')
        return redirect(url_for('login'))
    
    try:
        # Verificar que el archivo pertenece al usuario actual (para no-admins)
        if session.get('user_role') != 'admin':
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
        else:
            # Admin puede descargar cualquier archivo
            filepath = os.path.join('generated_documents', filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(filepath):
            # Si no existe, intentar regenerarlo
            flash('El archivo no existe. Regenerando...', 'warning')
            
            # Encontrar los datos del formulario para regenerar
            user_submissions = session.get('form_submissions', [])
            for submission in user_submissions:
                if submission.get('filename') == filename:
                    # Regenerar el archivo
                    form_data = submission.get('form_data', {})
                    form_type = submission.get('form_type')
                    
                    if form_type == 'acuerdo_seguridad':
                        filepath = generate_acuerdo_seguridad_file(form_data)
                    elif form_type == 'autorizacion_datos':
                        filepath = generate_autorizacion_datos_file(form_data)
                    
                    if os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True, download_name=filename)
            
            flash('No se pudo regenerar el archivo', 'error')
            return redirect(url_for('provider_dashboard'))
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        flash(f'Error al descargar el archivo: {str(e)}', 'error')
        return redirect(url_for('provider_dashboard'))

def generate_acuerdo_seguridad_file(form_data):
    """Genera el archivo de Acuerdo de Seguridad basado en la plantilla original"""
    try:
        # Usar ruta absoluta basada en la ubicación del script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(base_dir, 'generated_documents')
        
        # Crear directorio si no existe
        os.makedirs(docs_dir, exist_ok=True)
        
        filename = f"acuerdo_seguridad_{form_data.get('nit', 'sin_nit').replace('-', '')}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = os.path.join(docs_dir, filename)
        
        # Obtener fecha actual
        fecha_actual = datetime.now()
        
        content = f"""ACUERDO DE SEGURIDAD PROVEEDORES
INVERSIONES MONTANEL SAS

Estimado Asociado de Negocio: {form_data.get('razon_social', 'N/A')}

Con el objetivo de fortalecer las relaciones y garantizar el cumplimiento de los requisitos de seguridad, ambientales y sociales requeridos por la compañía, queremos recordarle los siguientes puntos:

1. Garantizar que el origen de los fondos no involucra actividades ilícitas propias o de terceras persona. Cumplir con los procedimientos y normas establecidas frente a la prevención y prohibición de lavado de activos, financiación al terrorismo, narcotráfico, contrabando de mercancías y tráfico ilegal de flora, soborno y corrupción.

2. Proteger de manera confidencial toda la información que le suministra la empresa Inversiones Montanel tanto en medio físico como electrónico evitando divulgar la información.

3. Mantener la integridad de la carga implementando controles de seguridad en los procesos de manipulación, empaque, almacenamiento, cargue, transporte, entrega de la flor, empaque o insumos y riegos de corrupción y soborno.

4. Reportar cualquier evento sospechoso que pueda afectar la integridad o cualquier situación anormal al responsable de seguridad o de SGSST de Inversiones Montanel SAS.

5. Notificar oportunamente a las autoridades competentes, si se detectan anomalías o actividades ilegales o sospechosas, relacionadas a faltantes o sobrantes de la carga de flor, entrega de insumos o empaque.

6. Cumplir con la legislación nacional respecto a criterios laborales, sociales y ambientales.

7. Suministrar los documentos, certificaciones y autorizaciones legales solicitados dentro del proceso de vinculación, como asociado de negocio (proveedor).

8. Notificar cualquier cambio de domicilio o lugar de operaciones de la empresa.

9. Mantener confidencialidad con los acuerdos comerciales firmados entre las partes.

10. Actualizar la información comercial anualmente como lo solicita la empresa usuaria.

11. Ser amigables con el medio ambiente mediante el desarrollo responsable de su actividad y la ejecución de programas y/o actividades que garanticen su preservación.

12. Ser amigables socialmente al cumplir con la legislación promoviendo el bienestar de los trabajadores y sus familias.

13. Capacitar al personal de su compañía en temas de seguridad.

En fe de lo anterior, los abajo firmantes, debidamente autorizados suscriben el presente Acuerdo con fecha del {fecha_actual.day} de {fecha_actual.strftime('%B')} del {fecha_actual.year}

================================================================================
POR EL ASOCIADO DE NEGOCIO:
================================================================================

RAZON SOCIAL: {form_data.get('razon_social', 'N/A')}
NIT: {form_data.get('nit', 'N/A')}
NOMBRE REPRESENTANTE LEGAL: {form_data.get('representante_legal', 'N/A')}
FIRMA: _______________________
DIRECCIÓN: {form_data.get('direccion', 'N/A')}
C.C No: {form_data.get('cedula_representante', 'N/A')}
TELEFONO: {form_data.get('telefono', 'N/A')}

================================================================================
POR LA EMPRESA USUARIA:
================================================================================

RAZON SOCIAL: INVERSIONES MONTANEL SAS
NIT: 860.009.240-2
NOMBRE REPRESENTANTE LEGAL: LAURA ARBOLEDA CALDERON
FIRMA: _______________________
DIRECCIÓN: CRA 12 A 83 75
C.C No: ________________
TELEFONO: 6951375 - 3182393272

================================================================================

Documento generado automáticamente el {fecha_actual.strftime('%d de %B del %Y a las %H:%M')}
Sistema de Gestión Documental - Inversiones Montanel SAS
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
        
    except Exception as e:
        print(f"Error generando archivo Acuerdo de Seguridad: {e}")
        return None

def generate_autorizacion_datos_file(form_data):
    """Genera el archivo de Autorización de Datos basado en la plantilla original"""
    try:
        # Usar ruta absoluta basada en la ubicación del script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(base_dir, 'generated_documents')
        
        # Crear directorio si no existe
        os.makedirs(docs_dir, exist_ok=True)
        
        filename = f"autorizacion_datos_{form_data.get('nit', 'sin_nit').replace('-', '')}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = os.path.join(docs_dir, filename)
        
        # Obtener fecha actual
        fecha_actual = datetime.now()
        
        content = f"""AUTORIZACIÓN TRATAMIENTO DE DATOS PERSONALES

En virtud de lo estipulado en la Ley 1581 del 2012 y demás normas concordantes; declaro que con la firma que precede autorizamos de forma expresa o inequívocamente a INVERSIONES MONTANEL SAS con NIT:860.009.240-2, para recolectar datos personales y realizar el tratamiento de datos de conformidad con lo establecido por la ley, para que realice verificación de la información suministrada y consulta en las diferentes bases o fuentes de información que considere necesarias para el cumplimiento de su política interna.

Inversiones Montanel SAS, en cumplimiento a la Ley 1581 de 2012, y nuestra política de privacidad, tratamiento y protección de datos personales informa que los datos personales (Incluyendo datos sensibles) suministrados en virtud del vínculo contraído con la empresa, serán tratados mediante el uso y mantenimiento de medidas de seguridad técnicas, humanas, físicas, administrativas y legales necesarias para otorgar seguridad a los registros evitando su adulteración, pérdida, consulta, uso o acceso no autorizado o fraudulento.

Además, INVERSIONES MONTANEL SAS actuará como responsable de tratamiento de datos personales del titular, los cuales podrá obtener y usar en actividades de operación, registro, además transferirlos internamente o a terceros, actualizarlos, suprimirlos y almacenarlos.

Es importante que como responsable de los datos conozca que tiene derechos legales especialmente el derecho a conocer, actualizar, rectificar y suprimir su información, también a revocar el consentimiento otorgado a través de la firma de esta autorización. Estos derechos pueden ser ejercidos mediante los siguientes canales:

- Correo electrónico enviado a info@montanel.com
- Vía telefónica llamando al 601-6951375 - 3182393272  
- Directamente en las oficinas ubicadas en la Cra 12 A 83 75 of 702.

Teniendo en cuenta lo anterior, acepto expresamente que los datos podrán ser procesados, recolectados, almacenados, utilizados, circulados, suprimidos, compartidos, actualizados y/o transmitidos, principalmente para fines comerciales, administrativos, financieros, de contacto y en general, para hacer posible la prestación de nuestros convenios comerciales o el cumplimiento de la normativa aplicable.

Con las mismas condiciones autorizo a la compañía INVERSIONES MONTANEL SAS para consultar ante cualquier entidad de información o en bases de datos la información y referencias que he declarado o que se requieran para prevenir y auto controlar el Lavado de Activos y la Financiación del Terrorismo como persona natural o de la persona jurídica que represento.

Se firma en la ciudad de {form_data.get('ciudad', '_____________')} a los {fecha_actual.day} días del mes de {fecha_actual.strftime('%B')} del año {fecha_actual.year}

Nombre Empresa: {form_data.get('razon_social', '_' * 50)}

Nit: {form_data.get('nit', '_' * 30)}

Firma: _______________________________________

Nombre Representante Legal: {form_data.get('representante_legal', '_' * 40)}

Identificación: {form_data.get('cedula_representante', '_' * 20)}

================================================================================

Documento generado automáticamente el {fecha_actual.strftime('%d de %B del %Y a las %H:%M')}
Sistema de Gestión Documental - Inversiones Montanel SAS
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
        
    except Exception as e:
        print(f"Error generando archivo Autorización de Datos: {e}")
        return None

# ===============================
# RUTAS DE REVISIÓN DE DOCUMENTOS
# ===============================

@app.route('/admin/documents')
def admin_review_documents():
    """Panel de revisión de documentos para admin"""
    if not session.get('user_email') or session.get('user_role') != 'admin':
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('login'))
    
    # Recopilar todos los documentos del sistema
    all_documents = []
    
    # Documentos de ejemplo para demostración
    sample_documents = [
        {
            'id': 'doc_001',
            'user_email': 'proveedor.demo@empresa.com',
            'company_name': 'Empresa Proveedor Demo S.A.S',
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
            'user_email': 'flores.valle@empresa.com',
            'company_name': 'Flores del Valle Ltda',
            'document_type': 'autorizacion_datos',
            'document_name': 'Autorización de Tratamiento de Datos',
            'filename': 'autorizacion_datos_987654321_20250102.txt',
            'created_at': '2025-01-02T14:15:00',
            'status': 'in_review',
            'priority': 'medium',
            'file_size': '18 KB'
        }
    ]
    
    # Agregar documentos reales de las sesiones
    current_user_email = session.get('user_email')
    
    # Simular documentos de otros usuarios (en producción esto vendría de la BD)
    for user_email in users_db:
        if user_email != current_user_email and users_db[user_email]['role'] != 'admin':
            # Simular algunos documentos para cada usuario
            user_profile = users_db[user_email].get('profile', {})
            company_name = user_profile.get('company_name', 'Empresa Sin Nombre')
            
            # Agregar documentos simulados
            all_documents.append({
                'id': f'real_{user_email}_acuerdo',
                'user_email': user_email,
                'company_name': company_name,
                'document_type': 'acuerdo_seguridad',
                'document_name': 'Acuerdo de Seguridad Proveedores',
                'filename': f'acuerdo_seguridad_{user_profile.get("nit", "000000000")}_20250103.txt',
                'created_at': '2025-01-03T09:00:00',
                'status': 'pending',
                'priority': 'medium',
                'file_size': '22 KB'
            })
    
    # Agregar documentos generados en la sesión actual
    user_submissions = session.get('form_submissions', [])
    for doc in user_submissions:
        all_documents.append({
            'id': f'session_{len(all_documents)}',
            'user_email': session.get('user_email'),
            'company_name': 'Usuario Actual',
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
    
    # Calcular estadísticas
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

@app.route('/admin/documents/<doc_id>')
def admin_document_detail(doc_id):
    """Vista detallada de un documento para revisión"""
    if not session.get('user_email') or session.get('user_role') != 'admin':
        flash('Acceso denegado. Solo para administradores.', 'error')
        return redirect(url_for('login'))
    
    # Buscar el documento (simulado por ahora)
    document = {
        'id': doc_id,
        'user_email': 'proveedor.demo@empresa.com',
        'company_name': 'Empresa Proveedor Demo S.A.S',
        'document_type': 'acuerdo_seguridad',
        'document_name': 'Acuerdo de Seguridad Proveedores',
        'filename': 'acuerdo_seguridad_123456789_20250102.txt',
        'created_at': '2025-01-02T10:30:00',
        'status': 'pending',
        'priority': 'high',
        'file_size': '25 KB',
        'form_data': {
            'razon_social': 'Empresa Proveedor Demo S.A.S',
            'nit': '123456789-0',
            'representante_legal': 'Juan Pérez García',
            'direccion': 'Calle 123 #45-67',
            'telefono': '601-2345678',
            'email': 'contacto@empresaproveedor.com'
        }
    }
    
    return render_template('admin/document_detail.html', document=document)

@app.route('/admin/documents/<doc_id>/update-status', methods=['POST'])
def update_document_status(doc_id):
    """Actualizar estado de un documento"""
    if not session.get('user_email') or session.get('user_role') != 'admin':
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        comments = data.get('comments', '')
        
        # Validar estados permitidos
        allowed_statuses = ['pending', 'in_review', 'approved', 'rejected']
        if new_status not in allowed_statuses:
            return jsonify({'error': 'Estado no válido'}), 400
        
        # Registrar la acción de revisión
        review_action = {
            'document_id': doc_id,
            'reviewer': session.get('user_email'),
            'action': new_status,
            'comments': comments,
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar en sesión (en producción iría a MongoDB)
        if 'review_actions' not in session:
            session['review_actions'] = []
        session['review_actions'].append(review_action)
        session.modified = True
        
        # Mensaje de éxito según la acción
        action_messages = {
            'pending': 'Documento marcado como pendiente',
            'in_review': 'Documento en proceso de revisión',
            'approved': 'Documento aprobado exitosamente',
            'rejected': 'Documento rechazado'
        }
        
        message = action_messages.get(new_status, f'Estado actualizado a {new_status}')
        
        return jsonify({
            'success': True,
            'message': message,
            'new_status': new_status
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/admin/documents/bulk-action', methods=['POST'])
def bulk_document_action():
    """Acciones en lote para múltiples documentos"""
    if not session.get('user_email') or session.get('user_role') != 'admin':
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        action = data.get('action')
        
        if not document_ids or not action:
            return jsonify({'error': 'Datos incompletos'}), 400
        
        # Procesar cada documento
        success_count = 0
        for doc_id in document_ids:
            # Registrar acción (en producción actualizaría BD)
            review_action = {
                'document_id': doc_id,
                'reviewer': session.get('user_email'),
                'action': action,
                'comments': f'Acción en lote: {action}',
                'timestamp': datetime.now().isoformat()
            }
            
            if 'review_actions' not in session:
                session['review_actions'] = []
            session['review_actions'].append(review_action)
            success_count += 1
        
        session.modified = True
        
        action_names = {
            'approved': 'aprobados',
            'rejected': 'rechazados',
            'in_review': 'marcados en revisión'
        }
        
        action_name = action_names.get(action, action)
        message = f'{success_count} documentos {action_name} exitosamente'
        
        return jsonify({
            'success': True,
            'message': message,
            'processed_count': success_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500
@app.route('/test')
def test():
    submissions_count = len(session.get('form_submissions', []))
    return f"""
    <h1>Flask funciona correctamente!</h1>
    <p>Usuarios registrados: {len(users_db)}</p>
    <p>Documentos generados en esta sesión: {submissions_count}</p>
    <a href="/">Ir al inicio</a>
    """

# Función auxiliar para obtener el usuario actual
@app.context_processor
def inject_user():
    current_user = None
    if session.get('user_email'):
        current_user = users_db.get(session['user_email'])
    return dict(current_user=current_user)

if __name__ == '__main__':
    print("Iniciando aplicación Flask...")
    print("Accede a: http://localhost:5000")
    print("Usuario admin: admin@montanel.com / admin123")
    print("Carpeta de documentos generados: ./generated_documents/")
    app.run(debug=True, host='0.0.0.0', port=5000)