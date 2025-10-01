import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_CONFIG

class EmailSender:
    def __init__(self):
        """
        初始化EmailSender
        
        参数:
            smtp_server: SMTP服务器地址，如果为None则使用config中的默认值
            smtp_port: SMTP端口
            username: 邮箱用户名
            password: 邮箱密码或授权码
        """
        from config import SMTP_CONFIG
        
        self.smtp_server = SMTP_CONFIG["163"]["server"]
        self.smtp_port = SMTP_CONFIG["163"]["port"]
        self.username = SMTP_CONFIG["163"]["username"]
        self.password = SMTP_CONFIG["163"]["password"]

    def send_email(self, to_email=None, subject=None, content=None, is_html=False):
        """
        发送电子邮件
        :param to_email: 收件人邮箱
        :param subject: 邮件主题
        :param content: 邮件内容
        :param is_html: 是否为HTML格式
        :return: 发送成功返回True，失败返回False
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加邮件正文
            if is_html:
                msg.attach(MIMEText(content, 'html'))
            else:
                msg.attach(MIMEText(content, 'plain'))
            
            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.username, self.password)
                server.send_message(msg)
                
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False

    def generate_stock_html(self, stock_notices, focus_stocks):
        """
        动态生成股票通知HTML
        :param stock_notices: 股票通知数组，格式如 ['拓尔思上涨了5.66%', ...]
        :param focus_stocks: 重点关注数组
        :return: 生成的HTML字符串
        """
        # 生成股票通知部分HTML
        stock_items = []
        for notice in stock_notices:
            # 解析股票名称和涨跌幅
            if "上涨" in notice:
                name = notice.split("上涨了")[0]
                change = float(notice.split("上涨了")[1].replace("%", ""))
                color = "#4CAF50"  # 绿色
            else:
                name = notice.split("下跌了")[0]
                change = float(notice.split("下跌了")[1].replace("%", ""))
                color = "#F44336"  # 红色
            
            stock_items.append(
                f"<div class='stock-item'>"
                f"{name}: <span style='color: {color}; font-weight: bold;'>"
                f"{change:.2f}%</span></div>"
            )
        
        # 生成重点关注部分HTML
        focus_items = []
        for stock in focus_stocks:
            focus_items.append(f"<div class='focus-item'>{stock}</div>")
        
        # 组合完整HTML（保持原有HTML模板不变）
        html_template = f"""
        <html>
        <head>
            <style>
                /* 保持原有样式不变 */
                body {{ font-family: Arial, sans-serif; }}
                .section {{ 
                    margin-bottom: 20px;
                    padding: 15px;
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #333;
                }}
                .stock-item {{
                    margin: 5px 0;
                    padding: 5px;
                    background-color: #fff;
                    border-left: 4px solid #4CAF50;
                }}
                .focus-item {{
                    margin: 5px 0;
                    padding: 5px;
                    background-color: #fff;
                    border-left: 4px solid #2196F3;
                }}
            </style>
        </head>
        <body>
            <div class="section">
                <div class="section-title">📈 股票通知</div>
                {"".join(stock_items)}
            </div>
            
            <div class="section">
                <div class="section-title">🔍 重点关注</div>
                {"".join(focus_items)}
            </div>
        </body>
        </html>
        """
        
        return html_template

# # 使用示例
# if __name__ == "__main__":
#     # 示例数据
#     stock_notices = [
#         "拓尔思上涨了5.66%",
#         "能科科技上涨了6.82%",
#         "赛意信息上涨了7.51%",
#         "创源股份下跌了2.37%"
#     ]
#     focus_stocks = ["中芯国际", "领益智造"]
    
#     # 生成HTML
#     html_content = generate_stock_html(stock_notices, focus_stocks)
    
#     # 发送邮件
#     # Hotmail/Outlook SMTP配置
#     sender = EmailSender(
#         smtp_server="smtp-mail.outlook.com",  # Hotmail/Outlook的SMTP服务器地址
#         smtp_port=587,                         # Hotmail/Outlook的SMTP端口
#         username="your_email@hotmail.com",     # 完整的Hotmail邮箱地址
#         password="your_password"               # 邮箱密码或应用专用密码
#     )
#     sender.send_email(
#         to_email="recipient@example.com",
#         subject="股票日报",
#         content=html_content,
#         is_html=True
#     )
