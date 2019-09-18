# Embedded Programming: Assembly Code Example
The following code gives a very simple example of an Assembly Language program. The aim of the example if to be simple (and short!) enough to be understood easily, while complex enough to be of use. Assembly language code executes faster than even its C counterpart, and is especially of use in embedded programming with FPGAs.

## Problem Description
For classification applications of machine learning, a confusion matrix (CM) is often used to quantify the performance of a model. A confusion matrix, in general, is a matrix of size $M\times M$ where $M$ is the number of classes.
$$CM = \begin{bmatrix}n_{11}&\cdots & n_{1M}\\
\vdots & \ddots & \vdots \\
n_{M1} & \cdots & n_{MM}
\end{bmatrix}$$

where $n_{ij}$ is the number of instances where a datapoint belonging to class $i$ was predicted by the model to be in class $j$. The confusion matrix is therefore always a square matrix, and a model is considered better if it has higher numbers along the diagonals (correct classifications) and lower numbers elsewhere.

The example assembly code aims to calculate the *probability of detection* $PD_m$ given a *confusion matrix* $CM$ for the class $m$. The probability of detection is defined mathematically as:
$$PD_m = \frac{n_{mm}}{\sum_{j=1}^M n_{mj}}$$
Intuitively, it is the probability of classifing class $m$ correctly.

## Code Structure
The code consists of three files:
1. `main.c`: The C program that defines the variables and calls the assembly code as an external function.
2. `pdm.s`: The assembly code which takes as input `CM` the confusion matrix, `M` the total number of classes and `m` the class for which $PD_m$ is calculated.
3. `cr_startup_lpc17.c`: A standard setup file (not written by me) that is used to initialize the program on an FPGA. This one is written for an LCP1769.

## Assembly Code Explanation
The assembly code can be divided into two parts: the main body and the `ELEMENT` subroutine.
1. The `ELEMENT` subroutine is designed to locate the address of $n_{mj}$ and extract the value at the location. To find $n_{mj}$, the formula $[a_{ij}] = [a_{11}] + (4M(i − 1)) + (4(j − 1))$ is used.
2. The main body of the `pdm` function uses a loop to perform the compuation of $\sum_{j=1}^M n_{mj}$ using the `ELEMENT` subroutine, accessing the elements in decreasing values of $j$. This sum is then multiplied by 10000 and then divided by $n_{mm}$. The multiplication by 10000 is done before being passed back to the C program to allow for the preservation of decimal points.