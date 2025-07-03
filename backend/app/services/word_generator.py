# backend/services/word_generator.py
from docxtpl import DocxTemplate
from datetime import datetime
import os

def generate_acuerdo_seguridad_word(form_data):
    """Genera documento usando la plantilla Word existente"""
    try:
        # Ubicar la plantilla
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, 'templates', 'word_templates', 
                                   'Formulario. ACUERDO DE SEGURIDAD PROVEEDORES INVERSIONES MONTANEL.docx')
        
        # Verificar que la plantilla existe
        if not os.path.exists(template_path):
            print(f"Plantilla no encontrada en: {template_path}")
            return None
        
        # Cargar la plantilla
        doc = DocxTemplate(template_path)
        
        # Preparar datos para la plantilla
        fecha_actual = datetime.now()
        
        # Mapear los datos del formulario a las variables de la plantilla
        context = {
            'razon_social': form_data.get('razon_social', ''),
            'razon_sociall': form_data.get('razon_social', ''),  # Por el typo en la plantilla
            'nit': form_data.get('nit', ''),
            'representante_legal': form_data.get('representante_legal', ''),
            'direccion': form_data.get('direccion', ''),
            'telefono': form_data.get('telefono', ''),
            'dia': fecha_actual.day,
            'mes': fecha_actual.strftime('%B'),  # Nombre completo del mes
            'año': fecha_actual.year
        }
        
        # Renderizar la plantilla con los datos
        doc.render(context)
        
        # Guardar el documento generado
        docs_dir = os.path.join(base_dir, 'generated_documents')
        os.makedirs(docs_dir, exist_ok=True)
        
        filename = f"acuerdo_seguridad_{form_data.get('nit', 'sin_nit').replace('-', '')}_{fecha_actual.strftime('%Y%m%d')}.docx"
        filepath = os.path.join(docs_dir, filename)
        
        doc.save(filepath)
        
        print(f"Documento generado exitosamente: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error generando documento desde plantilla: {e}")
        return None

def generate_autorizacion_datos_word(form_data):
    """Genera documento de autorización usando la plantilla Word existente"""
    try:
        # Ubicar la plantilla
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, 'templates', 'word_templates', 
                                   'Formulario. AUTORIZACION TRATAMIENTO DE DATOS PERSONALES IMO.docx')
        
        # Verificar que la plantilla existe
        if not os.path.exists(template_path):
            print(f"Plantilla no encontrada en: {template_path}")
            return None
        
        # Cargar la plantilla
        doc = DocxTemplate(template_path)
        
        # Preparar datos para la plantilla
        fecha_actual = datetime.now()
        
        # Mapear los datos del formulario a las variables de la plantilla
        context = {
            'razon_social': form_data.get('razon_social', ''),
            'nit': form_data.get('nit', ''),
            'representante_legal': form_data.get('representante_legal', ''),
            'cedula_representante': form_data.get('cedula_representante', ''),
            'ciudad': form_data.get('ciudad', ''),
            'dia': fecha_actual.day,
            'mes': fecha_actual.strftime('%B'),  # Nombre completo del mes
            'año': fecha_actual.year
        }
        
        # Renderizar la plantilla con los datos
        doc.render(context)
        
        # Guardar el documento generado
        docs_dir = os.path.join(base_dir, 'generated_documents')
        os.makedirs(docs_dir, exist_ok=True)
        
        filename = f"autorizacion_datos_{form_data.get('nit', 'sin_nit').replace('-', '')}_{fecha_actual.strftime('%Y%m%d')}.docx"
        filepath = os.path.join(docs_dir, filename)
        
        doc.save(filepath)
        
        print(f"Documento generado exitosamente: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error generando documento desde plantilla: {e}")
        return None