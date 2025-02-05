# -*- coding: utf-8 -*-

{
    'name': 'BAC Payment Acquirer',
    'category': 'Accounting/Payment',
    'summary': 'Payment Acquirer: BAC Implementation',
    'version': '3.0',
    'description': """BAC Payment Acquirer""",
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_bac_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'Other OSI approved licence',
}
