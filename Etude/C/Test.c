#include <stdio.h>
#include <math.h>
#include <stdbool.h>
/*
 * Name : Haoran MA
 * 
 * This is my first CSE 251 C program!!!
 */

// rlc.c
// 计算谐振频率
// 输入电容（微法）和电感（毫亨）
int main() {
    double microfarads, millihenrys;
    double capacitance, inductance;
    double frequency;

    // 输入电容和电感
    printf("Input Capacitance (microfarads): ");
    scanf("%lf", &microfarads);

    printf("Input Inductance (millihenrys): ");
    scanf("%lf", &millihenrys);

    // 单位换算
    capacitance = microfarads / 1e6;  // 转为法拉
    inductance = millihenrys / 1e3;   // 转为亨利

    // 计算谐振频率 f = 1 / (2π√(LC))
    frequency = 1.0 / (2 * M_PI * sqrt(inductance * capacitance));

    // 输出频率，保留三位小数
    printf("Resonant Frequency is %.3f\n", frequency);

    return 0;
}
