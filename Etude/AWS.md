[home](./AllForOne.MD)
## EC2
### EC2 实例与竞价实例

创建后可使用创建的秘钥对 使用ssh连接
Windows在可选功能中添加了openssh后可用powershell连接


```bash
# 创建自定义 AMI 的步骤
# 1. 启动一个 EC2 实例
aws ec2 run-instances --image-id ami-12345678 --count 1 --instance-type t2.micro --key-name MyKeyPair --security-group-ids sg-903004f8 --subnet-id subnet-6e7f829e

# 2. 配置实例（安装软件、修改配置等）

# 3. 创建 AMI
aws ec2 create-image --instance-id i-1234567890abcdef0 --name "MyCustomAMI" --description "An AMI for my application"
```
### 自定义 AMI
创建EC2 AMI 示例后 操作后保存自己的AMI镜像，包括了文件创建/下载软件/自启动服务设置 等等
可共享给别的Amazon账号，可使用第三方AMI
```bash
sudo systemctl enable --now nginx
```

### EBS(Elastic Block Store)
EBS 卷:
    可挂在到EC2实例上的**块存储设备**，类似真实的硬盘
EBS 快照:
    对挂载卷的备份，使用的是**增量备份**的方式

    - 从快照复制到卷
    //TO DO
    - 从快照复制到镜像
    类似AMI?数据都一样的，不确定服务设置是否保存

### Windows_EC2
    类型 协议 端口
使用 RDP TCP 3389 来连接
可Windows提供的**远程桌面**连接，但最常用还是RDP客户端

### Lambda 无服务器应用程序
- **并发和拓展控制**
- **触发器**: 可通过事件源（如 S3、DynamoDB、API Gateway）触发。
- **定义为容器镜像的函数**
- **代码签名**
- **函数蓝图**
- **数据库访问**
- **文件系统访问** 


### 配置测试事件
最初的测试事件: 提供JSON格式的请求
可在CloudWatch中看到对lambda函数的监控，包括日志等信息