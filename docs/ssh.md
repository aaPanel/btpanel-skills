1. 获取ssh服务状态：
   - uri: /safe/ssh/GetSshInfo
   - 响应信息： {
    "port": 22,
    "status": true,
    "status_text": "\u8fd0\u884c\u4e2d",
    "ping": true,
    "firewall_status": true,
    "fail2ban": {
        "status": 0,
        "installed": 0
    },
    "ban_cron_job": false
}
   - 其中 port:端口， status：服务状态， ping：是否支ping链接这台服务器， firewall_status：防火墙状态
   
2. 获取近期的ssh登录日志
    - uri: /mod/ssh/com/get_ssh_list
    - 参数 data=%7B%22search%22%3A%22%22%2C%22p%22%3A1%2C%22limit%22%3A10%2C%22select%22%3A%22ALL%22%2C%22historyType%22%3A%22ALL%22%7D
    - 参数中row表示每页条数，更具情况展示让AI可以使用
    - 响应: {
    "page": "<div><span class='Pcurrent'>1</span><a class='Pnum' href='/mod/ssh/com/get_ssh_list%3F?p=2'>2</a><a class='Pnum' href='/mod/ssh/com/get_ssh_list%3F?p=3'>3</a><a class='Pnum' href='/mod/ssh/com/get_ssh_list%3F?p=4'>4</a><a class='Pnum' href='/mod/ssh/com/get_ssh_list%3F?p=5'>5</a><a class='Pnext' href='/mod/ssh/com/get_ssh_list%3F?p=2'>\u4e0b\u4e00\u9875</a><a class='Pend' href='/mod/ssh/com/get_ssh_list%3F?p=5'>\u5c3e\u9875</a><span class='Pcount'>\u517150\u6761</span></div>",
    "shift": "0",
    "row": "10",
    "data": [
        {
            "timestamp": 1772442497,
            "time": "2026-03-02 17:08:17",
            "type": "success",
            "status": 1,
            "user": "root",
            "address": "192.168.168.156",
            "port": "52873",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772442497,
            "time": "2026-03-02 17:08:17",
            "type": "success",
            "status": 1,
            "user": "root",
            "address": "192.168.168.156",
            "port": "52872",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772423189,
            "time": "2026-03-02 11:46:29",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "43960",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772423189,
            "time": "2026-03-02 11:46:29",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "43960",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772423189,
            "time": "2026-03-02 11:46:29",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "43956",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772423189,
            "time": "2026-03-02 11:46:29",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "43956",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772419009,
            "time": "2026-03-02 10:36:49",
            "type": "success",
            "status": 1,
            "user": "root",
            "address": "192.168.168.65",
            "port": "30631",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772336794,
            "time": "2026-03-01 11:46:34",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "45502",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772336794,
            "time": "2026-03-01 11:46:34",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "45502",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        },
        {
            "timestamp": 1772336794,
            "time": "2026-03-01 11:46:34",
            "type": "failed",
            "status": 0,
            "user": "root",
            "address": "192.168.69.147",
            "port": "45498",
            "deny_status": 0,
            "login_type": "password",
            "area": {
                "country": {
                    "city": "",
                    "country": "\u5185\u7f51\u5730\u5740",
                    "en_short_code": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "operator": "",
                    "province": ""
                },
                "info": "\u5185\u7f51\u5730\u5740  "
            }
        }
    ]
}



