import smtplib
from email.mime.text import MIMEText

from allocation import config


class AbsNotifications:
    def send(self, destination, message):
        pass




class EmailNotifications(AbsNotifications):
    def __init__(
      self
    ):
        self.host = 'smtp.163.com'

        self.port = '465'
        self.sender = '18511041894@163.com'
        self.password = 'UPNHJWVYYCGTGPYL'

        # conf = config.get_email_host_and_port()
        # self.host = conf['host']
        # self.port = conf['port']
        # self.password = config.get_email_host_and_port()['password']
        self.sender = '18511041894@163.com'
        # self.server = smtplib.SMTP_SSL(smtp_host, port,)
        # self.server.login(self.sender,PASSWORD)
        # self.server.connect()

    def send(self, destination, msg):
        message = MIMEText(msg, 'plain', 'utf-8')
        subject = f'项目服务通知:{msg}'
        message['Subject'] = subject
        message['From'] = self.sender
        message['To'] = ','.join(destination)


        try:
            email_clint = smtplib.SMTP_SSL(self.host, self.port)
            print('获取证书成功')
            login_result = email_clint.login(self.sender, self.password)
            print('开始登陆')
            if login_result[0] == 235:
                print('登陆成功')
                result = email_clint.sendmail(
                    from_addr=self.sender,
                    to_addrs=destination,
                    msg=message.as_string())
                print(result)
                print('邮件发送成功')
                email_clint.quit()
            else:
                print('登陆失败')
        except Exception as e:
            print('发生错误', e)

