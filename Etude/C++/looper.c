#include <stdio.h>
#include <math.h>
#include <stdbool.h>

/* 
 * Simple program to experiment with looping
 */

int main()
{
    #include <stdio.h>

int main() {
    int f;
    int factorial;
    int done = 0;  // 控制循环是否结束的标志

    while (!done) {
        // 提示用户输入数字
        printf("Number to compute the factorial of: ");
        scanf("%d", &f);

        // 如果输入的是负数，退出程序
        if (f < 0) {
            done = 1;
        } else {
            // 处理特殊情况：0! = 1
            factorial = 1;  // 由于0!被定义为1

            // 计算大于0的数的阶乘
            if (f > 0) {
                for (int i = 1; i <= f; i++) {
                    factorial *= i;
                }
            }

            // 输出结果
            printf("%d! = %d\n", f, factorial);
        }
    }

    return 0;
}


