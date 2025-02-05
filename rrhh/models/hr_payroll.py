# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.release import version_info
import logging
import datetime
import time
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta as rdelta
from odoo.fields import Date, Datetime
from calendar import monthrange
from odoo.addons.l10n_gt_extra import a_letras
from odoo.exceptions import ValidationError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    porcentaje_prestamo = fields.Float(related="payslip_run_id.porcentaje_prestamo",string='Prestamo (%)',store=True)
    etiqueta_empleado_ids = fields.Many2many('hr.employee.category',string='Etiqueta empleado', related='employee_id.category_ids')
    cuenta_analitica_id = fields.Many2one('account.analytic.account','Cuenta analítica')

    # Dias trabajdas de los ultimos 12 meses hasta la fecha
    def dias_trabajados_ultimos_meses(self,empleado_id,fecha_desde,fecha_hasta):
        dias = {'days': 0}
        if empleado_id.contract_id.date_start:
            diferencia_meses = (fecha_hasta - fecha_desde)
            if empleado_id.contract_id.date_start <= fecha_hasta and empleado_id.contract_id.date_start >= fecha_desde:
                diferencia_meses = fecha_hasta - empleado_id.contract_id.date_start
        return diferencia_meses.days + 1

    def existe_entrada(self,entrada_ids,entrada_id):
        existe_entrada = False
        for entrada in entrada_ids:
            if entrada.input_type_id.id == entrada_id.id:
                existe_entrada = True
        return existe_entrada

    def compute_sheet(self):
        for nomina in self:
            mes_nomina = int(nomina.date_from.month)
            dia_nomina = int(nomina.date_to.day)
            anio_nomina = int(nomina.date_from.year)
            valor_pago = 0
            porcentaje_pagar = 0
            for entrada in nomina.input_line_ids:
                for prestamo in nomina.employee_id.prestamo_ids:
                    anio_prestamo = int(prestamo.fecha_inicio.year)
                    if (prestamo.codigo == entrada.input_type_id.code) and ((prestamo.estado == 'nuevo') or (prestamo.estado == 'proceso')):
                        lista = []
                        for lineas in prestamo.prestamo_ids:
                            if mes_nomina == int(lineas.mes) and anio_nomina == int(lineas.anio):
                                lista = lineas.nomina_id.ids
                                lista.append(nomina.id)
                                lineas.nomina_id = [(6, 0, lista)]
                                valor_pago = lineas.monto
                                porcentaje_pagar =(valor_pago * (nomina.porcentaje_prestamo/100))
                                entrada.amount = porcentaje_pagar
                        cantidad_pagos = prestamo.numero_descuentos
                        cantidad_pagados = 0
                        for lineas in prestamo.prestamo_ids:
                            if lineas.nomina_id:
                                cantidad_pagados +=1
                        if cantidad_pagados > 0 and cantidad_pagados < cantidad_pagos:
                            prestamo.estado = "proceso"
                        if cantidad_pagados == cantidad_pagos and cantidad_pagos > 0:
                            prestamo.estado = "pagado"
        res =  super(HrPayslip, self).compute_sheet()
        return res

    def _obtener_entrada(self,contrato_id, estructura_id):
        entradas = []
        entradas_estructura_planilla = []
        if contrato_id.structure_type_id and contrato_id.structure_type_id.default_struct_id:
            if contrato_id.structure_type_id.default_struct_id.input_line_type_ids:
                entradas = [entrada for entrada in contrato_id.structure_type_id.default_struct_id.input_line_type_ids]
        if estructura_id:
            if estructura_id.id != contrato_id.structure_type_id.default_struct_id.id:
                entradas_estructura_planilla = [entrada for entrada in estructura_id.input_line_type_ids]
        return entradas + entradas_estructura_planilla

    def calculo_rrhh(self,nomina):
        salario = self.salario_promedio(self.employee_id,self.date_to)
        dias = self.dias_trabajados_ultimos_meses(self.contract_id.employee_id,self.date_from,self.date_to)
        for entrada in self.input_line_ids:
            if entrada.input_type_id.code == 'SalarioPromedio':
                entrada.amount = salario
            if entrada.input_type_id.code == 'DiasTrabajados12Meses':
                entrada.amount = dias
            dias_calendario = monthrange(self.date_to.year, self.date_to.month)[1]
            if entrada.input_type_id.code == 'DiasCalendario':
                entrada.amount = dias_calendario
        return True

    # SALARIO PROMEDIO POR 12 MESES LABORADOS O MENOS
    def salario_promedio(self,empleado_id,fecha_final_nomina):
        historial_salario = []
        salario_meses = {}
        salario_total = 0
        salario_promedio_total = 0
        extra_ordinario_total = 0
        salario_completo = {}
        salario_sumatoria = 0
        if empleado_id.contract_ids[0].historial_salario_ids:
            posicion_historial = 0
            for linea in empleado_id.contract_ids[0].historial_salario_ids:
                if (posicion_historial+1) <= len(empleado_id.contract_ids[0].historial_salario_ids):
                    historial_salario.append({'salario': linea.salario, 'fecha':linea.fecha})
                    contador_mes_historial = 0

                    llave_salario = '01-'+str(linea.fecha.month)+'-'+str(linea.fecha.year)
                    llave_salario_fecha = datetime.datetime.strptime(str(llave_salario),'%d-%m-%Y').date()
                    llave_salario_fecha_str = '01-'+str(llave_salario_fecha.month)+'-'+str(llave_salario_fecha.year)
                    # index = empleado_id.contract_ids[0].historial_salario_ids.index(linea)
                    if posicion_historial+1 >= len(empleado_id.contract_ids[0].historial_salario_ids):
                        while llave_salario_fecha < fecha_final_nomina:
                            salario_completo[str(llave_salario_fecha_str)] = linea.salario
                            mes = relativedelta(months=1)
                            llave_salario_fecha = llave_salario_fecha + mes
                            llave_salario_fecha_str = '01-'+str(llave_salario_fecha.month)+'-'+str(llave_salario_fecha.year)
                            contador_mes_historial += 1

                        posicion_historial += 1
                    else:
                        while llave_salario_fecha < empleado_id.contract_ids[0].historial_salario_ids[posicion_historial+1].fecha:
                            salario_completo[str(llave_salario_fecha_str)] = linea.salario
                            mes = relativedelta(months=1)
                            llave_salario_fecha = llave_salario_fecha + mes
                            llave_salario_fecha_str = '01-'+str(llave_salario_fecha.month)+'-'+str(llave_salario_fecha.year)
                            contador_mes_historial += 1

                        posicion_historial += 1

            # historial_salario_ordenado = sorted(historial_salario, key=lambda k: k['fecha'],reverse=True)
            fecha_inicio_contrato = datetime.datetime.strptime(str(empleado_id.contract_ids[0].date_start),"%Y-%m-%d")
            fecha_final_contrato = datetime.datetime.strptime(str(fecha_final_nomina),"%Y-%m-%d")
            meses_laborados = (fecha_final_contrato.year - fecha_inicio_contrato.year) * 12 + (fecha_final_contrato.month - fecha_inicio_contrato.month)

            contador_mes = 0
            if meses_laborados >= 12:
                while contador_mes < 12:
                    mes = relativedelta(months=contador_mes)
                    resta_mes = fecha_final_contrato - mes
                    mes_letras = a_letras.mes_a_letras(resta_mes.month-1)
                    llave = '01-'+str(resta_mes.month)+'-'+str(resta_mes.year)
                    # llave_fecha = datetime.datetime.strptime(str(llave),'%Y-%m-%d')
                    salario = 0
                    if llave in salario_completo:
                        salario = salario_completo[llave]
                    salario_meses[llave] = {'nombre':mes_letras.upper(),'salario': salario,'anio':resta_mes.year,'extra':0,'total':0}
                    contador_mes += 1
                    salario_sumatoria += salario
            else:
                while contador_mes <= meses_laborados:
                    mes = relativedelta(months=contador_mes)
                    resta_mes = fecha_final_contrato - mes
                    mes_letras = a_letras.mes_a_letras(resta_mes.month-1)
                    llave = '01-'+str(resta_mes.month)+'-'+str(resta_mes.year)
                    salario = 0
                    if llave in salario_completo:
                        salario = salario_completo[llave]

                    salario_meses[llave] = {'nombre':mes_letras.upper(),'salario': salario,'anio':resta_mes.year,'extra':0,'total':0}
                    salario_sumatoria += salario
                    contador_mes += 1

            salario_promedio_total =  salario_sumatoria / len(salario_meses)
        else:
            salario_promedio_total = empleado_id.contract_ids[0].wage
        return salario_promedio_total


    def horas_sumar(self,lineas):
        horas = 0
        dias = 0
        for linea in lineas:
            tipo_id = self.env['hr.work.entry.type'].search([('id','=',linea['work_entry_type_id'])])
            if tipo_id and tipo_id.is_leave and tipo_id.descontar_nomina == False:
                horas += linea['number_of_hours']
                dias += linea['number_of_days']
        return {'dias':dias, 'horas': horas}

    def _get_worked_day_lines(self):
        res = super(HrPayslip, self)._get_worked_day_lines()
        tipos_ausencias_ids = self.env['hr.leave.type'].search([])
        datos = self.horas_sumar(res)
        ausencias_restar = []

        dias_ausentados_restar = 0
        contracts = False
        if self.employee_id.contract_id:
            contracts = self.employee_id.contract_id

        for ausencia in tipos_ausencias_ids:
            if ausencia.work_entry_type_id and ausencia.work_entry_type_id.descontar_nomina:
                ausencias_restar.append(ausencia.work_entry_type_id.id)

        trabajo_id = self.env['hr.work.entry.type'].search([('code','=','TRABAJO100')])
        for r in res:
            tipo_id = self.env['hr.work.entry.type'].search([('id','=',r['work_entry_type_id'])])
            if tipo_id and tipo_id.is_leave == False:
                r['number_of_hours'] += datos['horas']
                r['number_of_days'] += datos['dias']

            if len(ausencias_restar)>0:
                if r['work_entry_type_id'] in ausencias_restar:
                    dias_ausentados_restar += r['number_of_days']

        if contracts:
            dias_laborados = 0
            if contracts.schedule_pay == 'monthly':
                dias_laborados = 30
            if contracts.schedule_pay == 'bi-monthly':
                dias_laborados = 15

            dias_bonificacion = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(self.date_to), calendar=contracts.resource_calendar_id)

            if contracts.date_start and dias_bonificacion['days'] <= 31 and self.date_from <= contracts.date_start <= self.date_to:
                dias_laborados = dias_laborados - ((contracts.date_start - self.date_from  ).days)
                res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': dias_laborados - dias_ausentados_restar})
            elif dias_bonificacion['days'] > 150 and self.date_from >= contracts.date_start :
                res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': dias_bonificacion['days']+1})
            elif dias_bonificacion['days'] > 150 and self.date_from <= contracts.date_start <= self.date_to:
                dias_bonificacion = self.employee_id._get_work_days_data(Datetime.from_string(contracts.date_start), Datetime.from_string(self.date_to), calendar=contracts.resource_calendar_id)
                res.append({'work_entry_type_id': trabajo_id.id, 'sequence': 10, 'number_of_days': dias_bonificacion['days']+1})
            else:
                if contracts.schedule_pay == 'monthly':
                    if contracts.date_end and self.date_from <= contracts.date_end <= self.date_to:
                        dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(contracts.date_end), calendar=contracts.resource_calendar_id)
                        res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days':  dias_laborados['days'] + 1})
                    else:
                        total_dias = 30 - dias_ausentados_restar
                        res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': 0 if total_dias < 0 else total_dias})
                if contracts.schedule_pay == 'bi-monthly':
                    if contracts.date_end and self.date_from <= contracts.date_end <= self.date_to:
                        dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(contracts.date_end), calendar=contracts.resource_calendar_id)
                        res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days':  dias_laborados['days'] + 1})
                    else:
                        total_dias = 15 - dias_ausentados_restar
                        res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': 0 if total_dias < 0 else total_dias})
                # Cálculo de días para catorcena
                if contracts.schedule_pay == 'bi-weekly':
                    dias_laborados = self.employee_id._get_work_days_data(Datetime.from_string(self.date_from), Datetime.from_string(self.date_to), calendar=contracts.resource_calendar_id)
                    res.append({'work_entry_type_id': trabajo_id.id,'sequence': 10,'number_of_days': (dias_laborados['days']+1 - dias_ausentados_restar)})
        return res

    @api.onchange('employee_id','struct_id','contract_id', 'date_from', 'date_to','porcentaje_prestamo')
    def _onchange_employee(self):
        res = super(HrPayslip, self)._onchange_employee()
        mes_nomina = self.date_from.month
        anio_nomina = self.date_from.year
        dia_nomina = self.date_to.day
        entradas_nomina = []
        if self.contract_id:
            entradas = self._obtener_entrada(self.contract_id, self.struct_id)
            if self.contract_id.analytic_account_id:
                self.cuenta_analitica_id = self.contract_id.analytic_account_id.id
            if entradas:
                for entrada in entradas:
                    existe_entrada = False
                    if self.input_line_ids:
                        existe_entrada = self.existe_entrada(self.input_line_ids,entrada)
                    if existe_entrada == False:
                        entradas_nomina.append((0, 0, {'input_type_id':entrada.id}))
            if entradas_nomina:
                self.input_line_ids = entradas_nomina
            self.calculo_rrhh(self)

        for prestamo in self.employee_id.prestamo_ids:
            anio_prestamo = int(prestamo.fecha_inicio.year)
            for entrada in self.input_line_ids:
                if (prestamo.codigo == entrada.input_type_id.code) and ((prestamo.estado == 'nuevo') or (prestamo.estado == 'proceso')):
                    for lineas in prestamo.prestamo_ids:
                        if mes_nomina == int(lineas.mes) and anio_nomina == int(lineas.anio):
                            entrada.amount = lineas.monto*(self.porcentaje_prestamo/100)
        return res

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    porcentaje_prestamo = fields.Float('Prestamo (%)')

    def generar_pagos(self):
        pagos = self.env['account.payment'].search([('nomina_id', '!=', False)])
        nominas_pagadas = []
        for pago in pagos:
            nominas_pagadas.append(pago.nomina_id.id)
        for nomina in self.slip_ids:
            if nomina.id not in nominas_pagadas:
                total_nomina = 0
                if nomina.employee_id.diario_pago_id and nomina.employee_id.address_home_id and nomina.state == 'done':
                    res = self.env['report.rrhh.recibo'].lineas(nomina)
                    total_nomina = res['totales'][0] + res['totales'][1]
                    pago = {
                        'payment_type': 'outbound',
                        'partner_type': 'supplier',
                        'payment_method_id': 2,
                        'partner_id': nomina.employee_id.address_home_id.id,
                        'amount': total_nomina,
                        'journal_id': nomina.employee_id.diario_pago_id.id,
                        'nomina_id': nomina.id
                    }
                    pago_id = self.env['account.payment'].create(pago)
        return True
