# certbot-aliyun

自动申请 let‘s encrypt SSL 证书，调用阿里云 DNS API 验证

安装

```shell
apt install python3-venv
wget -O install.py https://github.com/yanxiangrong/certbot-aliyun/raw/main/script/install.py
python3 install.py
```

安装完成可以删除

```shell
rm install.py
```