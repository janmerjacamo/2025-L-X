# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter


class rrhh_libro_salarios(models.TransientModel):
    _name = 'rrhh.libro_salarios'

    anio = fields.Integer('Año', required=True)
    name = fields.Char('Nombre archivo')
    archivo = fields.Binary('Archivo')

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['anio'])
        res = res and res[0] or {}
        datas['form'] = res
        return self.env.ref('rrhh.action_libro_salarios').report_action([], data=datas)

    def print_report_excel(self):
        for w in self:
            dic = {}
            dic['anio'] = w['anio']
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            
            bold = libro.add_format({'bold': True})
            center = libro.add_format({'align': 'center'})
            text_wrap_bold = libro.add_format({'text_wrap': 'true', 'bold': True, 'align': 'center', 'valign': 'vcenter'})
            center_border_top = libro.add_format({'top': 1, 'align': 'center'})
            num_format = libro.add_format({'num_format': 'Q#,##0.00'})
            num_format_top = libro.add_format({'num_format': 'Q#,##0.00', 'top': 1,})
            date_format = libro.add_format({'num_format': 'dd/mm/yy', 'align': 'center'})
            
            ids = self.env.context.get('active_ids', [])
            for id_employee in ids:
                empleado = self.env['report.rrhh.libro_salarios']._get_empleado(id_employee)
                nominas = self.env['report.rrhh.libro_salarios']._get_nominas(id_employee,dic['anio'])
                fecha = self.env['report.rrhh.libro_salarios']._get_contrato(id_employee)
                hoja = libro.add_worksheet(empleado.name)
                
                hoja.write(1, 10, empleado.company_id.name)
                hoja.write(2, 10, empleado.company_id.vat)
                hoja.write(4, 8, 'LIBRO DE SALARIOS PARA TRABAJADORES PERMANENTES')
                hoja.write(6, 6, 'AUTORIZADO POR EL MINISTERIO DE TRABAJO Y PREVISION SOCIAL, SEGÚN ARTÍCULO 102 DEL CODIGO DE TRABAJO')
                
                hoja.write(8, 4, empleado.name, center)
                hoja.write(8, 7, empleado.edad, center)
                hoja.write(8, 10, 'Hombre' if empleado.gender == 'male' else 'Mujer', center)
                hoja.write(8, 13, empleado.country_id.name, center)
                hoja.write(8, 16, empleado.job_id.name, center)
                hoja.write(9, 4, 'Nombre del trabajador', center_border_top)
                hoja.write(9, 7, 'Edad', center_border_top)
                hoja.write(9, 10, 'Sexo', center_border_top)
                hoja.write(9, 13, 'Nacionalidad', center_border_top)
                hoja.write(9, 16, 'Ocupación', center_border_top)
                
                hoja.write(11, 4, empleado.igss, center)
                hoja.write(11, 7, empleado.identification_id, center)
                hoja.write(11, 10, fecha['fecha_ingreso'], date_format)
                hoja.write(11, 13, fecha['fecha_finalizacion'], date_format)
                hoja.write(12, 4, 'No. de afiliación al IGSS', center_border_top)
                hoja.write(12, 7, 'No. DPI ó permiso de Trabajo', center_border_top)
                hoja.write(12, 10, 'Fecha de Ingreso', center_border_top)
                hoja.write(12, 13, 'Fecha finalizac. de relación laboral', center_border_top)
                hoja.write(12, 16, 'Folio No.', bold)
                
                ordinario_total = 0
                extra_ordinario_total = 0
                otros_salarios_total = 0
                septimo_asueto_total = 0
                vacaciones_total = 0
                boni_incentivo_total = 0
                salario_total = 0
                igss_total = 0
                otras_deducciones_total = 0
                isr_total = 0
                total_deducciones = 0
                bono_agui_indem_total = 0
                boni_incentivo_decreto_total = 0
                dev_isr_otro_total = 0
                decreto_total = 0
                incentivo_decreto_total = 0
                liquido_total = 0
                
                
                hoja.write(15, 4, 'HORAS TRABAJADAS', bold)
                hoja.write(15, 7, 'SALARIO DEVENGADO', bold)
                hoja.write(15, 12, 'DEDUCCIONES LEGALES', bold)

                hoja.write(16, 0, 'No. de orden', text_wrap_bold)
                hoja.write(16, 1, 'Periodo de trabajo', text_wrap_bold)
                hoja.write(16, 2, 'Salario en Quetzales', text_wrap_bold)
                hoja.write(16, 3, 'Dias Trabajados', text_wrap_bold)
                hoja.write(16, 4, 'Ordinarias', text_wrap_bold)
                hoja.write(16, 5, 'Extraordinarias', text_wrap_bold)
                hoja.write(16, 6, 'Ordinario', text_wrap_bold)
                hoja.write(16, 7, 'Extraordinario', text_wrap_bold)
                hoja.write(16, 8, 'Otros salarios', text_wrap_bold)
                hoja.write(16, 9, 'Septimos y asuetos', text_wrap_bold)
                hoja.write(16, 10, 'Vacaciones', text_wrap_bold)
                hoja.write(16, 11, 'SALARIO TOTAL', text_wrap_bold)
                hoja.write(16, 12, 'Cuota laboral IGSS', text_wrap_bold)
                hoja.write(16, 13, 'Descuentos ISR', text_wrap_bold)
                hoja.write(16, 14, 'Otras deducciones', text_wrap_bold)
                hoja.write(16, 15, 'Total', text_wrap_bold)
                hoja.write(16, 16, 'Bonificación anual 42-92,Aguinaldo Decreto 76-78', text_wrap_bold)
                hoja.write(16, 17, 'Bonificación Incentivo Decreto 37-2001', text_wrap_bold)
                hoja.write(16, 18, 'Devoluciones I.S.R. y otras', text_wrap_bold)
                hoja.write(16, 19, 'Liquido a Recibir', text_wrap_bold)
                hoja.write(16, 20, 'Firma', text_wrap_bold)
                hoja.write(16, 21, 'Observaciones', text_wrap_bold)
                
                y = 17
                for nomina in nominas:
                    hoja.write(y, 0, nomina['orden'])
                    hoja.write(y, 1, str(nomina['fecha_inicio']) + ' - ' + str(nomina['fecha_fin']))
                    hoja.write(y, 2, nomina['salario'],num_format) 
                    hoja.write(y, 3, nomina['dias_trabajados'])
                    hoja.write(y, 4, nomina['ordinarias'])
                    hoja.write(y, 5, nomina['extra_ordinarias'])
                    hoja.write(y, 6, nomina['ordinario'], num_format) 
                    hoja.write(y, 7, nomina['extra_ordinario'], num_format)
                    hoja.write(y, 8, nomina['otros_salarios'], num_format)
                    hoja.write(y, 9, nomina['septimos_asuetos'], num_format)
                    hoja.write(y, 10, nomina['vacaciones'], num_format)
                    hoja.write(y, 11, nomina['total_salario_devengado'], num_format)
                    hoja.write(y, 12, nomina['igss'], num_format)
                    hoja.write(y, 13, nomina['isr'], num_format)
                    hoja.write(y, 14, nomina['otras_deducciones'], num_format)
                    hoja.write(y, 15, nomina['total_deducciones'], num_format)
                    hoja.write(y, 16, nomina['bono_agui_indem'], num_format)
                    hoja.write(y, 17, nomina['boni_incentivo_decreto'], num_format)
                    hoja.write(y, 18, nomina['dev_isr_otro'], num_format)
                    hoja.write(y, 19, nomina['liquido_recibir'], num_format)
                    
                    y += 1
                    ordinario_total += nomina['ordinario']
                    extra_ordinario_total += nomina['extra_ordinario']
                    otros_salarios_total += nomina['otros_salarios']
                    septimo_asueto_total += nomina['septimos_asuetos']
                    vacaciones_total += nomina['vacaciones']
                    salario_total += nomina['total_salario_devengado']
                    igss_total += nomina['igss']
                    isr_total += nomina['isr']
                    otras_deducciones_total += nomina['otras_deducciones']
                    total_deducciones += nomina['total_deducciones']
                    bono_agui_indem_total += nomina['bono_agui_indem']
                    boni_incentivo_decreto_total += nomina['boni_incentivo_decreto']
                    dev_isr_otro_total += nomina['dev_isr_otro']
                    liquido_total += nomina['liquido_recibir']
                
                hoja.write(y, 6, ordinario_total, num_format_top)
                hoja.write(y, 7, extra_ordinario_total, num_format_top)
                hoja.write(y, 8, otros_salarios_total, num_format_top)
                hoja.write(y, 9, septimo_asueto_total, num_format_top)
                hoja.write(y, 10, vacaciones_total, num_format_top)
                hoja.write(y, 11, salario_total, num_format_top)
                hoja.write(y, 12, igss_total, num_format_top)
                hoja.write(y, 13, isr_total, num_format_top)
                hoja.write(y, 14, otras_deducciones_total, num_format_top)
                hoja.write(y, 15, total_deducciones, num_format_top)
                hoja.write(y, 16, bono_agui_indem_total, num_format_top)
                hoja.write(y, 17, boni_incentivo_decreto_total, num_format_top)
                hoja.write(y, 18, dev_isr_otro_total, num_format_top)
                hoja.write(y, 19, liquido_total, num_format_top)
            
            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'Libro_salarios.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rrhh.libro_salarios',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
