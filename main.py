#-*- coding:utf-8 –*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import os
import json
import random
import time
import datetime
import traceback
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr


date_of_today = datetime.datetime.now()  # 当日日期
date_of_tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)  # 次日日期
current_folder = os.path.split(os.path.realpath(__file__))[0]  # 当前py文件路径
# 每日健康上报和入校申请URL
daily_report_url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/*default/index.do#/dailyReport'
enter_campus_apply_url = 'http://ehall.seu.edu.cn/qljfwapp3/sys/lwWiseduElectronicPass/*default/index.do'
server_chan_url = 'http://sc.ftqq.com/{}.send/'

def email_send(username, password, remote_email_addr, message):
    """
    用SEU邮箱发送上报结果至指定邮箱

    Args:
        username: 一卡通账号
        password: 一卡通密码
        remote_email_addr: 指定邮箱地址
        msg: 上报结果
    """
    if len(remote_email_addr) <=0 :
        return None

    seu_email_addr = str(username) + "@seu.edu.cn"
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['From'] = format_addr("SEU Daily Reporter {}".format(seu_email_addr))
    msg['To'] = format_addr("Admin {}".format(remote_email_addr))
    msg['Subject'] = Header("每日上报结果", "utf-8").encode()

    server = smtplib.SMTP_SSL("smtp.seu.edu.cn", 465)  # 启用SSL发信, 端口一般是465
    server.login(seu_email_addr, password)
    server.sendmail(seu_email_addr, [remote_email_addr], msg.as_string())
    server.quit()


def format_addr(s):
    """格式化地址.

    Args:
        s: str, 类似"SEU Daily Reporter <xxx@seu.edu.cn>"

    Returns:
        str, 类似"'=?utf-8?q?SEU Daily Reporter?= <xxx@seu.edu.cn>'"
    """
    name, addr = parseaddr(s)

    return formataddr((Header(name, 'utf-8').encode(), addr))

def server_chan_send(key, content, description):
    print(content, '\r\n', description)
    if len(key) <= 0:
        return None

    get_url = server_chan_url.format(key)
    param = dict()
    param['text'] = content
    param['desp'] = description.replace('\n', '\n\n')  # 将格式改为MarkDown格式
    return requests.get(get_url, param)  # 使用requests自带的编码库来避免url编码问题


def wait_element_by_class_name(drv, class_name, timeout):
    """等待某个class出现"""
    WebDriverWait(drv, timeout).until(lambda d: d.find_element_by_class_name(class_name))


def find_element_by_class_placeholder_keyword(drv, class_name, keyword):
    """用于找具有占位符的对话框"""
    elements = drv.find_elements_by_class_name(class_name)
    for element in elements:
        if element.get_attribute('placeholder').find(keyword) >= 0:  # 查找占位符
            return element

    return None


def find_element_by_class_keyword(drv, class_name, keyword):
    """寻找对话框/普通按钮"""
    elements = drv.find_elements_by_class_name(class_name)
    for element in elements:
        if element.text.find(keyword) >= 0:  # 查找文本
            return element

    return None


def select_default_item_by_keyword(drv, keyword):
    """在入校申请时选择默认项"""
    items = drv.find_elements_by_class_name('emapm-item')  # 找到所有项目
    for item in items:
        if item.text.find(keyword) >= 0:  # 找到项目标题
            drv.execute_script("arguments[0].scrollIntoView();", item)  # 滚动页面直到元素可见
            item.click()

    wait_element_by_class_name(drv, 'mint-picker__confirm', 5)  # 等待弹出动画
    time.sleep(1)
    find_element_by_class_keyword(drv, 'mint-picker__confirm', '确定').click()  # 点击确定
    time.sleep(1)


def select_default_item_in_areas(drv, keyword):
    """在入校申请时选择通行区域"""
    items = drv.find_elements_by_class_name('emapm-item')  # 找到所有项目
    for item in items:
        if item.text.find(keyword) >= 0:  # 找到项目标题
            drv.execute_script("arguments[0].scrollIntoView();", item)  # 滚动页面直元素可见
            item.click()

    wait_element_by_class_name(drv, 'mint-checkbox-new-row', 5)  # 等待弹出动画
    time.sleep(1)
    drv.find_element_by_class_name('mint-checkbox-new-row').click()  # 点击复选框
    time.sleep(1)
    find_element_by_class_keyword(drv, 'mint-selected-footer-confirm', '确定').click()  # 点击确定按钮
    time.sleep(1)


def picker_click(drv, column, cnt):
    """选择滚轮的中的项目"""
    pickers = column.find_elements_by_class_name('mt-picker-column-item')  # 所有滚动元素
    drv.execute_script("arguments[0].scrollIntoView();", pickers[cnt])  # 滚动页面直元素可见
    pickers[cnt].click()  # 选中元素


def time_date_reason_pick(drv, cfg):
    """选择通行时间及申请理由"""
    items = drv.find_elements_by_class_name('emapm-item')  # 找到所有项目
    for item in items:
        if item.text.find('通行开始时间') >= 0:  # 找到项目标题
            drv.execute_script("arguments[0].scrollIntoView();", item)  # 滚动页面直元素可见
            item.click()  # 点击项目
            columns = item.find_elements_by_class_name('mint-picker-column')  # 找到项目内所有滚轮
            time.sleep(1)
            picker_click(drv, columns[0], date_of_tomorrow.date().year - 1920)  # 年 从1920年开始
            picker_click(drv, columns[1], date_of_tomorrow.date().month - 1)  # 月 从1开始
            picker_click(drv, columns[2], date_of_tomorrow.date().day - 1)  # 日 从1开始
            picker_click(drv, columns[3], 7)  # 时
            picker_click(drv, columns[4], 31)  # 分 入校时间为7时31分
            time.sleep(1)
            find_element_by_class_keyword(drv, 'mint-picker__confirm', '确定').click()  # 点击确定按钮
            time.sleep(1)

        if item.text.find('通行结束时间') >= 0:  # 找到项目标题
            drv.execute_script("arguments[0].scrollIntoView();", item)  # 滚动页面直元素可见
            item.click()  # 点击项目
            columns = item.find_elements_by_class_name('mint-picker-column')  # 找到项目内所有滚轮
            time.sleep(1)
            picker_click(drv, columns[0], date_of_tomorrow.date().year - 1920)  # 年 从1920年开始
            picker_click(drv, columns[1], date_of_tomorrow.date().month - 1)  # 月 从1开始
            picker_click(drv, columns[2], date_of_tomorrow.date().day - 1)  # 日 从1开始
            picker_click(drv, columns[3], 21)  # 时
            picker_click(drv, columns[4], 59)  # 分 出校时间为21时59分
            time.sleep(1)
            find_element_by_class_keyword(drv, 'mint-picker__confirm', '确定').click()  # 点击确定按钮
            time.sleep(1)

        if item.text.find('申请理由') >= 0:  # 找到项目标题
            drv.execute_script("arguments[0].scrollIntoView();", item)  # 滚动页面直元素可见
            item.click()  # 点击项目
            column = item.find_element_by_class_name('mint-picker-column')  # 找到项目内所有滚轮
            time.sleep(1)
            picker_click(drv, column, cfg['reasons'][date_of_tomorrow.date().weekday()])  # 根据星期自动填写目的
            time.sleep(1)
            find_element_by_class_keyword(drv, 'mint-picker__confirm', '确定').click()  # 点击确定按钮
            time.sleep(1)


def check_todays_report(drv):
    """检查当日是否已进行过入校申请"""
    items = drv.find_elements_by_class_name('res-list')  # 找到所有已填报项目
    latest = find_element_by_class_keyword(items[0], 'res-item-ele', '申请时间').text  # 第一个项目即为最近一次的填报
    latest = latest[latest.find(' ') + 1: latest.rfind(' ')]  # 只保留日期
    latest_date = datetime.datetime.strptime(latest, '%Y-%m-%d').date()  # 转换

    if latest_date == date_of_today.date():  # 今日已经填报过了
        return True

    return False


def login(drv, cfg):
    """登录"""
    username_input = drv.find_element_by_id('username')  # 账户输入框
    password_input = drv.find_element_by_id('password')  # 密码输入框
    login_button = find_element_by_class_keyword(drv, 'auth_login_btn', '登录')  # 登录按钮
    if login_button is None:
        login_button = find_element_by_class_keyword(drv, 'auth_login_btn', 'Sign in')  # 登录按钮

    username_input.send_keys(cfg['username'])
    password_input.send_keys(cfg['password'])
    login_button.click()  # 登录账户


def daily_report(drv, cfg):
    """进行每日上报"""
    # 新增填报
    wait_element_by_class_name(drv, 'mint-loadmore-top', 30)  # 等待界面加载 超时30s
    time.sleep(1)
    add_btn = drv.find_element_by_xpath('//*[@id="app"]/div/div[1]/button[1]')  # 找到新增按钮
    if add_btn.text == '退出':
        result_msg = str(cfg['username']) + ' 今日已经进行过健康上报！'
        server_chan_send(cfg['server_chan_key'], result_msg, '')
        email_send(cfg['username'], cfg['password'], cfg['email_addr'],  result_msg)
        return
    else:
        add_btn.click()  # 点击新增填报按钮
        time.sleep(3)  # 等待界面动画

    # 输入体温
    temp_input = find_element_by_class_placeholder_keyword(drv, 'mint-field-core', '请输入当天晨检体温')
    drv.execute_script("arguments[0].scrollIntoView();", temp_input)  # 滚动页面直元素可见
    temp_input.click()  # 点击输入框
    temp = random.randint(int(cfg['temp_range'][0] * 10), int(cfg['temp_range'][1] * 10))  # 产生随机体温
    temp_input.send_keys(str(temp / 10))  # 输入体温
    time.sleep(1)

    # 点击提交按钮并确认
    find_element_by_class_keyword(drv, 'mint-button--large', '确认并提交').click()  # 点击提交按钮
    wait_element_by_class_name(drv, 'mint-msgbox-confirm', 5)  # 等待弹出动画
    time.sleep(1)
    find_element_by_class_keyword(drv, 'mint-msgbox-confirm', '确定').click()  # 点击确认按钮

    result_msg =  str(cfg['username']) + ' 每日健康上报成功!\r\n' + "今日体温填报：" + str(temp / 10) + "℃"
    server_chan_send(cfg['server_chan_key'], result_msg, '')
    email_send(cfg['username'], cfg['password'], cfg['email_addr'],  result_msg)


def enter_campus_apply(drv, cfg):
    """进行入校申请"""
    wait_element_by_class_name(drv, 'res-item-ele', 30)  # 等待界面加载 超时30s

    if check_todays_report(drv):  # 今日已进行入校申请
        result_msg = str(cfg['username']) + ' 今日已经进行过入校申请！'
        server_chan_send(cfg['server_chan_key'], result_msg, '')
        email_send(cfg['username'], cfg['password'], cfg['email_addr'],  result_msg)
        return

    drv.find_element_by_xpath('//*[@id="app"]/div/div[3]').click()  # 找到新增按钮

    time.sleep(2)  # 等待窗口动画弹出
    popup = find_element_by_class_keyword(drv, 'mint-msgbox-confirm', '确定')  # 查询是否弹出了对话框
    if popup is not None:  # 如果弹出了对话框
        result_msg = str(cfg['username']) + ' 当前不在入校申请填报时间!'
        server_chan_send(cfg['server_chan_key'], result_msg, '')
        email_send(cfg['username'], cfg['password'], cfg['email_addr'],  result_msg)
        return

    wait_element_by_class_name(drv, 'emapm-item', 30)  # 等待界面加载
    select_default_item_by_keyword(drv, '身份证件类型')
    select_default_item_by_keyword(drv, '工作场所是否符合防护要求')
    select_default_item_by_keyword(drv, '工作人员能否做好个人防护')
    select_default_item_by_keyword(drv, '是否已在南京居家隔离')
    select_default_item_by_keyword(drv, '目前身体是否健康')

    select_default_item_in_areas(drv, '通行区域')  # 填写通行区域

    time_date_reason_pick(drv, cfg)  # 填入入校时间/出校时间/入校理由

    temp_input = find_element_by_class_placeholder_keyword(drv, 'mint-field-core', '请输入所到楼宇')
    drv.execute_script("arguments[0].scrollIntoView();", temp_input)  # 滚动页面直元素可见
    temp_input.click()  # 点击输入框
    temp_input.send_keys(cfg['places'][date_of_tomorrow.weekday()])  # 输入入校地址

    find_element_by_class_keyword(drv, 'tg-button', '提交').click()  # 点击提交按钮
    wait_element_by_class_name(drv, 'mint-msgbox-confirm', 5)  # 等待弹出动画
    time.sleep(1)
    find_element_by_class_keyword(drv, 'mint-msgbox-confirm', '确定').click()  # 点击确认按钮

    result_msg = str(cfg['username'])+' 每日入校申请成功!'
    server_chan_send(cfg['server_chan_key'], result_msg, '')
    email_send(cfg['username'], cfg['password'], cfg['email_addr'],   result_msg)


def run(profile, config):
    if config["browser"] == "chrome":
        driver = webdriver.Chrome(executable_path=os.path.join(current_folder, "chromedriver.exe"))
    elif config["browser"] == "firefox":
        driver = webdriver.Firefox(executable_path=os.path.join(current_folder, "geckodriver.exe"))
    try:
        # 打开健康填报网站
        driver.get(daily_report_url)
        # 登录
        login(driver, profile)
        # 每日填报
        daily_report(driver, profile)
        # 打开入校申请网站
        if config["enable_enter_campus_apply"]:
            time.sleep(5)
            driver.get(enter_campus_apply_url)
            # 填写入校申请
            enter_campus_apply(driver, profile)
    except Exception:
        exception = traceback.format_exc()
        result_msg = profile['username'] + ' 出错啦,请尝试手动重新填报'
        server_chan_send(profile['server_chan_key'], result_msg, exception)
        email_send(cfg['username'], cfg['password'], cfg['email_addr'], result_msg)
    finally:
        time.sleep(3)
        driver.quit()  # 退出整个浏览器


if __name__ == '__main__':
    with open(os.path.join(current_folder, 'config.json'), encoding='UTF-8') as config_file:
        j = json.load(config_file)
        users = j['users']
        cfg = j['config']

        for user in users:
            print(user['username'], '正在填报...')
            run(user, cfg)
            print(user['username'], '填报完成')
            time.sleep(1)
