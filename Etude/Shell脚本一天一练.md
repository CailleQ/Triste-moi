## Shell 脚本一天一练
[home](./AllForOne.MD)
### sed
`sed` 是一种流编辑器，用于对输入流（文件或管道输入）执行基本的文本转换。


```bash
# 将文件中所有的 'foo' 替换为 'bar'
sed 's/foo/bar/g' input.txt

# 删除文件中的第 2 行
sed '2d' input.txt
```

### grep
`grep` 是一个命令行工具，用于在纯文本数据中搜索匹配正则表达式的行。

  
```bash
# 在文件中搜索包含 'error' 的行
grep 'error' log.txt

# 递归搜索目录中的所有文件
grep -r 'error' /path/to/directory
```

### awk
`awk` 是一种编程语言，专为文本处理设计，通常用于数据提取和报表生成。

  
```bash
# 打印文件的第二列
awk '{print $2}' data.txt

# 计算文件中第二列的总和
awk '{sum += $2} END {print sum}' data.txt


```