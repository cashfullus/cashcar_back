from appConfig.routes import app

if __name__ == '__main__':
    app.run(ssl_context=('/etc/letsencrypt/live/app.api.service.cashcarplus.com/fullchain.pem', '/etc/letsencrypt/live/app.api.service.cashcarplus.com/privkey.pem'))
