% Calculating the first terms of the Fibonacci sequence
% The terms are tabulated at the address fibtab
% fibtab[0] = 0
% fibtab[1] = Fib(1) = 1
% fibtab[2] = Fib(2) = 1
% etc.
%
% r0 is the address of Fib(n)
% r1 contains Fib(n-2)
% r2 contains Fib(n-1)
% r3 contains Fib(n) = Fib(n-1) + Fib(n-2)
%
% 
            mov r1, #0
			mov r0, #fibtab   % fibtab[0] = 0
			str r1, [r0]
			mov r2, #1
			add r0, r0, #1    % fibtab[1]
			str r2, [r0]      % Fib(1) = 1
			add r0, r0, #1
@loop		add r3, r2, r1    % fibtab[n] = fibtab[n-1] + fibtab[n-2]
			str r3, [r0]
			add r0, r0, #1    % n = n + 1
			cmp r0, #endtab   % Stop if array is full
			blt continue
			b fin
@continue	mov r1, r2        % Fib(n-1) becomes Fib(n-2)
			mov r2, r3        % Fib(n) becomes Fib(n-1)
			b loop
@fin        b fin

@fibtab		rmw 20         % reserving an array of 20 elements
@endtab		smw 0xFFFF     % sentinel, (cannot be passed, the element before needs to be calculated)
