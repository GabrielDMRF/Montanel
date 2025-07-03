# Agregar al archivo existente
@forms_bp.route('/acuerdo-seguridad', methods=['GET', 'POST'])
def acuerdo_seguridad():
    if not require_login():
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            from app.services.document_generator import DocumentGenerator
            
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
            
            generator = DocumentGenerator()
            user_data = {'email': session.get('user_email')}
            
            filepath, filename = generator.generate_acuerdo_seguridad(form_data, user_data)
            
            # Guardar en sesión
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
            
            flash('¡Documento generado exitosamente!', 'success')
            return redirect(url_for('provider_dashboard'))
            
        except Exception as e:
            flash(f'Error al generar el documento: {str(e)}', 'error')
            return render_template('provider/forms/acuerdo_seguridad.html')
    
    return render_template('provider/forms/acuerdo_seguridad.html')