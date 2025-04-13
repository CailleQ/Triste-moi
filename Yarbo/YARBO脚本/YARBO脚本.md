[home](./AllForOne.MD)

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

