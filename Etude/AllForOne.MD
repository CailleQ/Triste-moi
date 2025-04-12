# Continuel
创建仓库，每日提交
尝试实现页面跳转，将此页面改成目录
//想法：梳理/集合 FSE常用手册
## 面试准备
[查看 面试准备 相关笔记](./面试准备.md)
## Fondation

## AWS
[查看 AWS 相关笔记](./AWS.md)
## 网络/网安
[查看 网络/网安 相关笔记](./网络_网安.md)
## Algorithm

## Shell script (运维)

### Shell脚本一天一练
[Shell脚本一天一练](./Shell脚本一天一练.md)

### YARBO脚本
- **my.sh.YARBO**: 用于连接到 YARBO 服务器。
- **my.sh**: 用于连接到 firefly 服务器。
- **my.sh.firefly**: 也是用于连接到 firefly 服务器的脚本。

```bash
cat my.sh.YARBO 
dst=$1
ssh -o 'proxycommand socat - PROXY:127.0.0.1:%h:%p,proxyport=6000' YARBO@${dst}.yb.com
```

```bash
cat my.sh
dst=$1
ssh -o 'proxycommand socat - PROXY:127.0.0.1:%h:%p,proxyport=6000' firefly@${dst}.yb.com
```

```bash
cat my.sh.firefly 
dst=$1
ssh -o 'proxycommand socat - PROXY:127.0.0.1:%h:%p,proxyport=6000' firefly@${dst}.yb.com
```






