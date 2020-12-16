import smtplib
from email.mime.text import MIMEText


class SendEmail(object):
    def __init__(self):
        self.host = 'smtp.163.com'

        self.port = '465'
        self.sender = '18511041894@163.com'
        self.password = 'UPNHJWVYYCGTGPYL'

    def send_email(self, receiver, subject='', body=''):
        message = MIMEText(body, 'plain', 'utf-8')

        message['From'] = self.sender
        message['To'] = ','.join(receiver)
        message['Subject'] = subject


        try:
            email_clint = smtplib.SMTP_SSL(self.host, self.port)
            print('获取证书成功')
            login_result = email_clint.login(self.sender, self.password)
            print('开始登陆')
            if login_result[0] == 235:
                print('登陆成功')
                result = email_clint.sendmail(self.sender, receiver, message.as_string())
                print(result)
                print('邮件发送成功')
                email_clint.quit()
            else:
                print('登陆失败')
        except Exception as e:
            print('发生错误', e)

def send(msg):
    SendEmail().send_email(['18511041894@163.com',], '12-09-提醒', msg)
