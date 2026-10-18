# Run inside the Odoo container (see README). Prints a 90-day API key for the admin user: copy it into .env yourself.
import datetime
user = env.ref('base.user_admin')
key = env['res.users.apikeys'].with_user(user)._generate(None, 'msp-ops-copilot', datetime.datetime.now() + datetime.timedelta(days=90))
print('APIKEY::' + key)
env.cr.commit()
