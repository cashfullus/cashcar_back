from routes import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50123)
    #, ssl_context=('/etc/letsencrypt/live/app.api.service.cashcarplus.com/fullchain.pem', '/etc/letsencrypt/live/app.api.service.cashcarplus.com/privkey.pem')
