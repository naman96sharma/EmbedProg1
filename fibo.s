% Calculating Fib(6)
@begin mov r0, #6
       bl  r7, fib
@end   b   end
 
% Rend dans r0 Fib(r0)
@fib   cmp r0,#1      % compare n with 1
       mov r1,#1      % fibo <-- 1 : Fib(1)
       mov r2,#1      % fiboPrev <-- 1 : Fib(2)
       blt ret        % if n < 1, finish
       beq ret        % if n <= 1, finish
       mov r3,#2      % i <-- 2
@loop  cmp r0,r3      % compare n with i
       blt ret        % if n < i, break loop
       beq ret        % if n <= i, break loop
       mov r4,r1      % temp <-- fibo
       add r1,r1,r2   % fibo <-- fibo + fiboPrev
       mov r2,r4      % fiboPrev <-- temp
       add r3,r3,#1   % i <-- i + 1
       b loop         % continue loop
@ret   mov r0,r1      % Put result in r0.
       b r7
