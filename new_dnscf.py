import requests
import traceback
import time
import os
import json
import re

# API 密钥
CF_API_TOKEN    =   str(os.environ["CF_API_TOKEN"])
CF_ZONE_ID      =   str(os.environ["CF_ZONE_ID"])
CF_DNS_NAME     =   str(os.environ["CF_DNS_NAME"])

# pushplus_token
PUSHPLUS_TOKEN  =   str(os.environ["PUSHPLUS_TOKEN"])



headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            # 发送 GET 请求，设置超时
            #response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            response2 = requests.get('https://cf.090227.xyz/', timeout=timeout)
            print("response2：",str(response2.text))
            # 获取网页内容
            html_content = response2.text

            # 匹配 IPv4 地址
            ip_addresses = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", html_content)

            # 去重 IP 地址
            unique_ip_addresses = set(ip_addresses)
            ip_list = list(unique_ip_addresses)
            # 打印去重后的 IP 地址
            print("最终ip:",ip_list[:3])
            
            if response2.status_code == 200:
                return ip_list[:3]
        except Exception as e:
            traceback.print_exc()
            print(f"get_cf_speed_test_ip Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            
            # 检查响应状态码
            # if response.status_code == 200:
                # return response.text
        # except Exception as e:
            # traceback.print_exc()
            # print(f"get_cf_speed_test_ip Request failed (attempt {attempt + 1}/{max_retries}): {e}")
    # 如果所有尝试都失败，返回 None 或者抛出异常，根据需要进行处理
    return None

# 获取 DNS 记录
def get_dns_records(name,ip_list):
    ip_list = ip_list
    del_ip_list = []
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    response = requests.get(url, headers=headers)
    #print("response：",str(response.json()))
    if response.status_code == 200:
        records = response.json()['result']
        for record in records:
            if record['name'] == name:
                if record['content'] in ip_list:
                    ip_list.remove(record['content'])
                else:
                    del_ip_list.append(record['id'])
                    # delete_url = "{}/{}".format(url, record['id'])
                    # delete_response = requests.delete(delete_url,headers=headers)
                    # if delete_response.json()["success"]:
                        # print("成功删除 DNS 记录", record["name"],record['content'])
                    # else:
                        # print("删除 DNS 记录失败")
        return ip_list,del_ip_list,records
    else:
        print('Error fetching DNS records:', response.text)

# 更新 DNS 记录
def update_dns_record(name, cf_ip):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    print("要更新cf的ip：",cf_ip)
    data = {
        "type": 'A',
        "name": str(name),
        "content": cf_ip,
        #"ttl": None,
        "proxied": False,
    }

    response = requests.post(url, headers=headers, json=data)
    #print(8888889,response.json())
    if response.status_code == 200:
        print(f"cf_dns_change success: ---- Time: " + str(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " ---- ip：" + str(cf_ip))
        return "ip:" + str(cf_ip) + "解析" + str(name) + "成功"
    else:
        e = ""
        traceback.print_exc()
        print(f"cf_dns_change ERROR: ---- Time: " + str(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " ---- MESSAGE: " + str(e))
        return "ip:" + str(cf_ip) + "解析" + str(name) + "失败"

# 消息推送
def push_plus(content):
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "IP优选DNSCF推送",
        "content": content,
        "template": "markdown",
        "channel": "wechat"
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)
#删除云端的ip
def del_ip(name,del_ip_list,records):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    for record in records:
        if record['name'] == name:
            if record['id'] in del_ip_list:
                print("在删除云端的id：",record['id'])
                delete_url = "{}/{}".format(url, record['id'])
                delete_response = requests.delete(delete_url,headers=headers)
                if delete_response.json()["success"]:
                    print("成功删除 DNS 记录", record["name"],record['content'])
                else:
                    print("删除 DNS 记录失败")
# 主函数
def main():
    # 获取最新优选IP
    ip_addresses_str = get_cf_speed_test_ip()
    #print("ip_addresses_str：",str(ip_addresses_str))
    # ip_addresses = ip_addresses_str.split(',')
    ip_addresses = ip_addresses_str
    print("获取到的优选ip列表：",str(ip_addresses))
    ip_list,del_ip_list,records = get_dns_records(CF_DNS_NAME,ip_addresses)
    print("要更新的ip(并排除云端重复ip)：",str(ip_list))
    print("云端要删除的id：",str(del_ip_list))#,records)
    push_plus_content = []
    if not ip_list:
      return
    # 遍历 IP 地址列表
    for index, ip_address in enumerate(ip_addresses):
        # 执行 DNS 变更
        dns = update_dns_record(CF_DNS_NAME, ip_address)
        push_plus_content.append(dns)
    del_ip(CF_DNS_NAME,del_ip_list,records)
    push_plus('\n'.join(push_plus_content))
    
    

if __name__ == '__main__':
    main()
