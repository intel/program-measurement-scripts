# mark_description "Intel(R) C Intel(R) 64 Compiler XE for applications running on Intel(R) 64, Version 12.1.1.256 Build 2011101";
# mark_description "1";
# mark_description "-vec-report -c -O3 -Wall -Wextra -funroll-loops -S -ftree-vectorizer-verbose=9 -cl-unsafe-math-optimizations";
# mark_description " -v";
	.file "load_procedure.c"
	.text
..TXTST0:
# -- Begin  load
# mark_begin;
       .align    16,0x90
	.globl load
load:
# parameter 1: %rdi
# parameter 2: %esi
# parameter 3: %xmm0
# parameter 4: %rdx
# parameter 5: %rcx
# parameter 6: %r8d
# parameter 7: %r9
# parameter 8: 240 + %rsp
# parameter 9: 248 + %rsp
..B1.1:                         # Preds ..B1.0
..___tag_value_load.1:                                          #10.1
        pushq     %r15                                          #10.1
..___tag_value_load.3:                                          #
        pushq     %rbx                                          #10.1
..___tag_value_load.5:                                          #
        pushq     %rbp                                          #10.1
..___tag_value_load.7:                                          #
        subq      $208, %rsp                                    #10.1
..___tag_value_load.9:                                          #
        movq      %rdx, %r10                                    #10.1
        cvttsd2si %xmm0, %rbx                                   #13.21
        shrl      $3, %esi                                      #17.43
        xorl      %r15d, %r15d                                  #24.33
        movl      240(%rsp), %r11d                              #10.1
        pxor      %xmm7, %xmm7                                  #20.13
        rdtsc                                                   #27.19
        movl      %edx, %edx                                    #27.19
        movl      %eax, %eax                                    #27.19
        shlq      $32, %rdx                                     #27.19
        orq       %rdx, %rax                                    #27.19
        lea       (%rdi,%rsi,8), %rbp                           #18.34
        movsbl    (%r9), %edx                                   #29.10
        testl     %edx, %edx                                    #29.10
        movslq    %r11d, %rsi                                   #22.20
        je        ..B1.60       # Prob 10%                      #29.10
                                # LOE rax rcx rbp rsi rdi r9 r10 r12 r13 r14 ebx r8d r11d r15d xmm0 xmm7
..B1.2:                         # Preds ..B1.1
        movl      %r11d, %edx                                   #71.46
        movaps    %xmm0, %xmm5                                  #76.33
        shlq      $3, %rdx                                      #71.69
        movaps    %xmm0, %xmm4                                  #76.83
        imulq     248(%rsp), %rdx                               #71.69
        movq      %rdx, 168(%rsp)                               #71.69
        fildq     168(%rsp)                                     #71.69
        shrq      $63, %rdx                                     #71.69
        movsd     .L_2il0floatpacket.11(%rip), %xmm6            #61.18
        movsd     .L_2il0floatpacket.9(%rip), %xmm2             #72.97
        subsd     %xmm6, %xmm5                                  #76.33
        addsd     %xmm6, %xmm4                                  #76.83
        faddl     .L_2il0floatpacket.12(,%rdx,8)                #71.69
        movl      %r11d, %edx                                   #
        shrl      $31, %edx                                     #
        fstpl     200(%rsp)                                     #71.69
        addl      %r11d, %edx                                   #
        movsd     200(%rsp), %xmm3                              #71.69
        movsd     .L_2il0floatpacket.10(%rip), %xmm1            #72.131
        sarl      $1, %edx                                      #
        movsd     %xmm1, 32(%rsp)                               #
        movsd     %xmm2, 40(%rsp)                               #
        movsd     %xmm3, 24(%rsp)                               #
        movsd     %xmm4, 56(%rsp)                               #
        movsd     %xmm5, 192(%rsp)                              #
        movsd     %xmm6, 112(%rsp)                              #
        movsd     %xmm7, 120(%rsp)                              #
        movsd     %xmm0, 64(%rsp)                               #
        movq      %rdi, 184(%rsp)                               #
        movl      %edx, 72(%rsp)                                #
        movq      %rax, 80(%rsp)                                #
        movq      %rsi, 88(%rsp)                                #
        movl      %r11d, 96(%rsp)                               #
        movq      %r10, 104(%rsp)                               #
        movl      %r8d, 176(%rsp)                               #
        movq      %r12, (%rsp)                                  #
..___tag_value_load.10:                                         #
        movq      %rcx, %r12                                    #
        movq      %r13, 8(%rsp)                                 #
..___tag_value_load.11:                                         #
        movl      $17, %r13d                                    #
        movq      %r14, 16(%rsp)                                #
..___tag_value_load.12:                                         #
        movq      %r9, %r14                                     #
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.3:                         # Preds ..B1.58 ..B1.2
        xorl      %edi, %edi                                    #39.85
        cmpl      %ebx, %r13d                                   #39.85
        movq      184(%rsp), %r8                                #31.25
        lea       -17(%rbx), %r10d                              #39.49
        adcl      $0, %edi                                      #39.85
        imull     %edi, %r10d                                   #39.85
        movq      (%r12), %rsi                                  #34.46
        movq      %rsi, %r11                                    #34.46
        rdtsc                                                   #36.33
        movl      %edx, %ecx                                    #36.33
        movl      %eax, %r9d                                    #36.33
        cmpq      %rbp, %r8                                     #41.24
        jae       ..B1.44       # Prob 10%                      #41.24
                                # LOE rcx rbp rsi r8 r9 r10 r11 r12 r14 ebx r13d r15d
..B1.4:                         # Preds ..B1.3
        movl      %ecx, 136(%rsp)                               #59.15
        movq      %r11, 144(%rsp)                               #59.15
        movl      %r15d, 152(%rsp)                              #59.15
        movl      %ebx, 160(%rsp)                               #59.15
        movl      %ebx, %edi                                    #59.15
        movl      %r9d, 128(%rsp)                               #59.15
        movsd     112(%rsp), %xmm0                              #59.15
        movsd     120(%rsp), %xmm1                              #59.15
        movl      72(%rsp), %ebx                                #59.15
        movq      80(%rsp), %rcx                                #59.15
        movq      88(%rsp), %r15                                #59.15
        movl      96(%rsp), %r13d                               #59.15
        movq      104(%rsp), %r11                               #59.15
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.5:                         # Preds ..B1.42 ..B1.4
        movsbl    (%r14), %eax                                  #41.50
        testl     %eax, %eax                                    #41.50
        je        ..B1.43       # Prob 20%                      #41.50
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.6:                         # Preds ..B1.5
        testq     %r15, %r15                                    #46.20
        jle       ..B1.36       # Prob 10%                      #46.20
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.7:                         # Preds ..B1.6
        movq      (%r11), %rax                                  #49.7
        cmpl      $6, %r13d                                     #46.4
        lea       1(%rax), %rdx                                 #
        jle       ..B1.29       # Prob 50%                      #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.8:                         # Preds ..B1.7
        cmpq      %r8, %r11                                     #48.13
        jbe       ..B1.10       # Prob 50%                      #48.13
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.9:                         # Preds ..B1.8
        movq      %r11, %rsi                                    #48.13
        lea       (,%r15,8), %r9                                #48.13
        subq      %r8, %rsi                                     #48.13
        cmpq      %r9, %rsi                                     #48.13
        jge       ..B1.12       # Prob 50%                      #48.13
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.10:                        # Preds ..B1.8 ..B1.9
        cmpq      %r11, %r8                                     #48.13
        jbe       ..B1.29       # Prob 50%                      #48.13
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.11:                        # Preds ..B1.10
        movq      %r8, %rsi                                     #48.13
        subq      %r11, %rsi                                    #48.13
        cmpq      $8, %rsi                                      #48.13
        jl        ..B1.29       # Prob 50%                      #48.13
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.12:                        # Preds ..B1.9 ..B1.11
        cmpq      $8, %r15                                      #46.4
        jl        ..B1.61       # Prob 10%                      #46.4
                                # LOE rax rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.13:                        # Preds ..B1.12
        movq      %r8, %rdx                                     #46.4
        andq      $15, %rdx                                     #46.4
        movl      %edx, %r9d                                    #46.4
        testl     %r9d, %r9d                                    #46.4
        je        ..B1.16       # Prob 50%                      #46.4
                                # LOE rax rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r9d r13d xmm0 xmm1
..B1.14:                        # Preds ..B1.13
        testl     $7, %r9d                                      #46.4
        jne       ..B1.61       # Prob 10%                      #46.4
                                # LOE rax rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.15:                        # Preds ..B1.14
        movl      $1, %r9d                                      #46.4
                                # LOE rax rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r9d r13d xmm0 xmm1
..B1.16:                        # Preds ..B1.15 ..B1.13
        movl      %r9d, %esi                                    #46.4
        lea       8(%rsi), %rdx                                 #46.4
        cmpq      %rdx, %r15                                    #46.4
        jl        ..B1.61       # Prob 10%                      #46.4
                                # LOE rax rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r9d r13d xmm0 xmm1
..B1.17:                        # Preds ..B1.16
        negl      %r9d                                          #46.4
        addl      %r13d, %r9d                                   #46.4
        andl      $7, %r9d                                      #46.4
        negl      %r9d                                          #46.4
        addl      %r13d, %r9d                                   #46.4
        movslq    %r9d, %rdx                                    #46.4
        xorl      %r9d, %r9d                                    #46.4
        testq     %rsi, %rsi                                    #46.4
        jbe       ..B1.21       # Prob 0%                       #46.4
                                # LOE rax rdx rcx rbp rsi rdi r8 r9 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.19:                        # Preds ..B1.17 ..B1.19
        incq      %rax                                          #49.7
        addsd     (%r8,%r9,8), %xmm1                            #48.5
        incq      %r9                                           #46.4
        cmpq      %rsi, %r9                                     #46.4
        jb        ..B1.19       # Prob 82%                      #46.4
                                # LOE rax rdx rcx rbp rsi rdi r8 r9 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.21:                        # Preds ..B1.19 ..B1.17
        lea       (%r8,%rsi,8), %r9                             #
        pxor      %xmm2, %xmm2                                  #20.13
        movsd     %xmm1, %xmm2                                  #20.13
        pxor      %xmm1, %xmm1                                  #20.13
                                # LOE rax rdx rcx rbp rsi rdi r8 r9 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1 xmm2
..B1.22:                        # Preds ..B1.22 ..B1.21
        addpd     (%r9), %xmm2                                  #48.5
        addpd     16(%r9), %xmm1                                #48.5
        addpd     32(%r9), %xmm2                                #48.5
        addpd     48(%r9), %xmm1                                #48.5
        addq      $8, %rsi                                      #46.4
        addq      $64, %r9                                      #46.4
        addq      $8, %rax                                      #20.13
        cmpq      %rdx, %rsi                                    #46.4
        jb        ..B1.22       # Prob 82%                      #46.4
                                # LOE rax rdx rcx rbp rsi rdi r8 r9 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1 xmm2
..B1.23:                        # Preds ..B1.22
        addpd     %xmm1, %xmm2                                  #20.13
        movaps    %xmm2, %xmm1                                  #20.13
        unpckhpd  %xmm2, %xmm1                                  #20.13
        addsd     %xmm1, %xmm2                                  #20.13
        movaps    %xmm2, %xmm1                                  #20.13
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.24:                        # Preds ..B1.23 ..B1.61
        cmpq      %r15, %rdx                                    #46.4
        jae       ..B1.28       # Prob 0%                       #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.26:                        # Preds ..B1.24 ..B1.26
        incq      %rax                                          #49.7
        addsd     (%r8,%rdx,8), %xmm1                           #48.5
        incq      %rdx                                          #46.4
        cmpq      %r15, %rdx                                    #46.4
        jb        ..B1.26       # Prob 82%                      #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.28:                        # Preds ..B1.26 ..B1.24
        movq      %rax, (%r11)                                  #49.7
        jmp       ..B1.35       # Prob 100%                     #49.7
                                # LOE rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.29:                        # Preds ..B1.7 ..B1.10 ..B1.11
        movl      $1, %r9d                                      #46.4
        xorl      %esi, %esi                                    #46.4
        testl     %ebx, %ebx                                    #46.4
        jbe       ..B1.33       # Prob 0%                       #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx esi r9d r13d xmm0 xmm1
..B1.30:                        # Preds ..B1.29
        pxor      %xmm2, %xmm2                                  #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx esi r13d xmm0 xmm1 xmm2
..B1.31:                        # Preds ..B1.31 ..B1.30
        addq      $2, %rax                                      #49.7
        lea       (%rsi,%rsi), %r9d                             #48.5
        movslq    %r9d, %r9                                     #48.13
        incl      %esi                                          #46.4
        addsd     (%r8,%r9,8), %xmm1                            #48.5
        movq      %rdx, (%r11)                                  #49.7
        addq      $2, %rdx                                      #49.7
        cmpl      %ebx, %esi                                    #46.4
        addsd     8(%r8,%r9,8), %xmm2                           #48.5
        movq      %rax, (%r11)                                  #49.7
        jb        ..B1.31       # Prob 64%                      #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx esi r13d xmm0 xmm1 xmm2
..B1.32:                        # Preds ..B1.31
        addsd     %xmm2, %xmm1                                  #46.4
        lea       1(%rsi,%rsi), %r9d                            #46.4
                                # LOE rax rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r9d r13d xmm0 xmm1
..B1.33:                        # Preds ..B1.32 ..B1.29
        cmpl      %r13d, %r9d                                   #46.4
        ja        ..B1.35       # Prob 50%                      #46.4
                                # LOE rax rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r9d r13d xmm0 xmm1
..B1.34:                        # Preds ..B1.33
        movslq    %r9d, %r9                                     #48.13
        incq      %rax                                          #49.7
        addsd     -8(%r8,%r9,8), %xmm1                          #48.5
        movq      %rax, (%r11)                                  #49.7
                                # LOE rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.35:                        # Preds ..B1.34 ..B1.33 ..B1.28
        movq      (%r12), %rsi                                  #52.6
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.36:                        # Preds ..B1.35 ..B1.6
        incq      %rsi                                          #52.6
        lea       (%r8,%r15,8), %r8                             #54.4
        movq      %rsi, (%r12)                                  #52.6
        rdtsc                                                   #56.39
        movl      %edx, %edx                                    #56.39
        movl      %eax, %eax                                    #56.39
        shlq      $32, %rdx                                     #56.39
        orq       %rdx, %rax                                    #56.39
        movq      %rax, %rdx                                    #56.22
        subq      %rcx, %rdx                                    #56.22
        cmpq      %r10, %rdx                                    #56.70
        jae       ..B1.40       # Prob 10%                      #56.70
                                # LOE rax rdx rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.38:                        # Preds ..B1.36 ..B1.38
        rdtsc                                                   #56.39
        movl      %edx, %edx                                    #56.39
        movl      %eax, %eax                                    #56.39
        shlq      $32, %rdx                                     #56.39
        orq       %rdx, %rax                                    #56.39
        movq      %rax, %rdx                                    #56.22
        subq      %rcx, %rdx                                    #56.22
        cmpq      %r10, %rdx                                    #56.70
        jb        ..B1.38       # Prob 82%                      #56.70
                                # LOE rax rdx rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.40:                        # Preds ..B1.38 ..B1.36
        movq      %rax, %rcx                                    #57.4
        cmpq      %rdi, %rdx                                    #59.15
        jae       ..B1.42       # Prob 50%                      #59.15
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.41:                        # Preds ..B1.40
        movaps    %xmm1, %xmm2                                  #61.18
        movaps    %xmm1, %xmm3                                  #61.23
        addsd     %xmm0, %xmm2                                  #61.18
        movaps    %xmm2, %xmm1                                  #61.23
        divsd     %xmm3, %xmm1                                  #61.23
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.42:                        # Preds ..B1.41 ..B1.40
        cmpq      %rbp, %r8                                     #41.24
        jb        ..B1.5        # Prob 82%                      #41.24
                                # LOE rcx rbp rsi rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.43:                        # Preds ..B1.5 ..B1.42
        movq      %rcx, 80(%rsp)                                #
        movl      $17, %r13d                                    #
        movsd     %xmm1, 120(%rsp)                              #
        movl      128(%rsp), %r9d                               #
        movl      136(%rsp), %ecx                               #
        movq      144(%rsp), %r11                               #
        movl      152(%rsp), %r15d                              #
        movl      160(%rsp), %ebx                               #
                                # LOE rcx rbp rsi r9 r11 r12 r14 ebx r13d r15d
..B1.44:                        # Preds ..B1.43 ..B1.3
        rdtsc                                                   #65.14
        movl      %edx, %edx                                    #65.14
        movl      %eax, %eax                                    #65.14
        shlq      $32, %rdx                                     #65.14
        orq       %rdx, %rax                                    #65.14
        shlq      $32, %rcx                                     #36.33
        orq       %rcx, %r9                                     #36.33
        subq      %r9, %rax                                     #65.14
        movq      %rax, 168(%rsp)                               #67.31
        fildq     168(%rsp)                                     #67.31
        movq      %rsi, 168(%rsp)                               #67.52
        fildq     168(%rsp)                                     #67.52
        shrq      $63, %rax                                     #67.31
        movq      %r11, 168(%rsp)                               #67.74
        fildq     168(%rsp)                                     #67.74
        fxch      %st(2)                                        #67.31
        faddl     .L_2il0floatpacket.12(,%rax,8)                #67.31
        shrq      $63, %rsi                                     #67.52
        shrq      $63, %r11                                     #67.74
        fstpl     200(%rsp)                                     #67.3
        movsd     200(%rsp), %xmm2                              #67.3
        cmpl      $0, 176(%rsp)                                 #69.8
        faddl     .L_2il0floatpacket.12(,%rsi,8)                #67.52
        fstpl     200(%rsp)                                     #67.3
        movsd     200(%rsp), %xmm1                              #67.3
        faddl     .L_2il0floatpacket.12(,%r11,8)                #67.74
        fstpl     200(%rsp)                                     #67.3
        movsd     200(%rsp), %xmm0                              #67.3
        subsd     %xmm0, %xmm1                                  #67.74
        divsd     %xmm1, %xmm2                                  #67.74
        jne       ..B1.46       # Prob 78%                      #69.8
                                # LOE rbp r12 r14 ebx r13d r15d xmm2
..B1.45:                        # Preds ..B1.44
        movsd     24(%rsp), %xmm1                               #71.91
        movl      $.L_2__STRING.0, %edi                         #72.4
        divsd     %xmm2, %xmm1                                  #71.91
        movsd     40(%rsp), %xmm0                               #72.4
        movl      %ebx, %esi                                    #72.4
        mulsd     %xmm1, %xmm0                                  #72.4
        movl      $3, %eax                                      #72.4
        mulsd     32(%rsp), %xmm1                               #72.4
        movsd     %xmm2, 48(%rsp)                               #72.4
..___tag_value_load.13:                                         #72.4
        call      printf                                        #72.4
..___tag_value_load.14:                                         #
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.68:                        # Preds ..B1.45
        movsd     48(%rsp), %xmm2                               #
                                # LOE rbp r12 r14 ebx r13d r15d xmm2
..B1.46:                        # Preds ..B1.68 ..B1.44
        comisd    192(%rsp), %xmm2                              #76.33
        jb        ..B1.48       # Prob 50%                      #76.33
                                # LOE rbp r12 r14 ebx r13d r15d xmm2
..B1.47:                        # Preds ..B1.46
        movsd     56(%rsp), %xmm0                               #76.83
        comisd    %xmm2, %xmm0                                  #76.83
        jae       ..B1.58       # Prob 50%                      #76.83
                                # LOE rbp r12 r14 ebx r13d r15d xmm2
..B1.48:                        # Preds ..B1.47 ..B1.46
        comisd    64(%rsp), %xmm2                               #77.28
        jbe       ..B1.53       # Prob 50%                      #77.28
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.49:                        # Preds ..B1.48
        testl     %ebx, %ebx                                    #79.14
        jbe       ..B1.58       # Prob 50%                      #79.14
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.50:                        # Preds ..B1.49
        testl     %r15d, %r15d                                  #81.38
        jle       ..B1.64       # Prob 11%                      #81.38
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.51:                        # Preds ..B1.50
        xorl      %r15d, %r15d                                  #81.41
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.52:                        # Preds ..B1.51 ..B1.64
        movl      %r15d, %ecx                                   #83.53
        movl      $1, %eax                                      #83.53
        sarl      $1, %ecx                                      #83.53
        movl      $1, %esi                                      #85.5
        shrl      $30, %ecx                                     #83.53
        xorl      %edx, %edx                                    #85.5
        addl      %r15d, %ecx                                   #83.53
        shrl      $2, %ecx                                      #83.53
        negl      %ecx                                          #83.53
        shll      %cl, %eax                                     #83.53
        subl      %eax, %ebx                                    #83.5
        testl     %ebx, %ebx                                    #85.5
        cmovle    %edx, %esi                                    #85.5
        imull     %esi, %ebx                                    #85.32
        jmp       ..B1.58       # Prob 100%                     #85.32
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.53:                        # Preds ..B1.48
        cmpl      $1000000, %ebx                                #90.14
        jae       ..B1.58       # Prob 50%                      #90.14
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.54:                        # Preds ..B1.53
        testl     %r15d, %r15d                                  #92.38
        jl        ..B1.56       # Prob 23%                      #92.38
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.55:                        # Preds ..B1.54
        cmpl      $24, %r15d                                    #93.75
        lea       1(%r15), %eax                                 #93.75
        cmovl     %eax, %r15d                                   #93.75
        jmp       ..B1.57       # Prob 100%                     #93.75
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.56:                        # Preds ..B1.54
        xorl      %r15d, %r15d                                  #92.41
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.57:                        # Preds ..B1.56 ..B1.55
        movl      %r15d, %ecx                                   #94.47
        movl      $1, %eax                                      #94.47
        sarl      $1, %ecx                                      #94.47
        shrl      $30, %ecx                                     #94.47
        addl      %r15d, %ecx                                   #94.47
        shrl      $2, %ecx                                      #94.47
        shll      %cl, %eax                                     #94.47
        addl      %eax, %ebx                                    #94.5
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.58:                        # Preds ..B1.47 ..B1.52 ..B1.49 ..B1.57 ..B1.53
                                #      
        movsbl    (%r14), %eax                                  #29.10
        testl     %eax, %eax                                    #29.10
        jne       ..B1.3        # Prob 82%                      #29.10
                                # LOE rbp r12 r14 ebx r13d r15d
..B1.59:                        # Preds ..B1.58
        movsd     120(%rsp), %xmm7                              #
        movq      (%rsp), %r12                                  #
..___tag_value_load.15:                                         #
        movq      8(%rsp), %r13                                 #
..___tag_value_load.16:                                         #
        movq      16(%rsp), %r14                                #
..___tag_value_load.17:                                         #
                                # LOE r12 r13 r14 xmm7
..B1.60:                        # Preds ..B1.59 ..B1.1
        movaps    %xmm7, %xmm0                                  #100.9
        addq      $208, %rsp                                    #100.9
..___tag_value_load.18:                                         #
        popq      %rbp                                          #100.9
..___tag_value_load.20:                                         #
        popq      %rbx                                          #100.9
..___tag_value_load.22:                                         #
        popq      %r15                                          #100.9
..___tag_value_load.24:                                         #
        ret                                                     #100.9
..___tag_value_load.25:                                         #
                                # LOE
..B1.61:                        # Preds ..B1.12 ..B1.16 ..B1.14 # Infreq
        xorl      %edx, %edx                                    #46.4
        jmp       ..B1.24       # Prob 100%                     #46.4
                                # LOE rax rdx rcx rbp rdi r8 r10 r11 r12 r14 r15 ebx r13d xmm0 xmm1
..B1.64:                        # Preds ..B1.50                 # Infreq
        cmpl      $-24, %r15d                                   #82.82
        lea       -1(%r15), %eax                                #82.82
        cmovg     %eax, %r15d                                   #82.82
        jmp       ..B1.52       # Prob 100%                     #82.82
        .align    16,0x90
..___tag_value_load.32:                                         #
                                # LOE rbp r12 r14 ebx r13d r15d
# mark_end;
	.type	load,@function
	.size	load,.-load
	.data
# -- End  load
	.section .rodata, "a"
	.align 16
	.align 16
.L_2il0floatpacket.12:
	.long	0x00000000,0x00000000,0x00000000,0x43f00000
	.type	.L_2il0floatpacket.12,@object
	.size	.L_2il0floatpacket.12,16
	.align 8
.L_2il0floatpacket.9:
	.long	0x00000000,0x3e100000
	.type	.L_2il0floatpacket.9,@object
	.size	.L_2il0floatpacket.9,8
	.align 8
.L_2il0floatpacket.10:
	.long	0x00000000,0x3eb00000
	.type	.L_2il0floatpacket.10,@object
	.size	.L_2il0floatpacket.10,8
	.align 8
.L_2il0floatpacket.11:
	.long	0x00000000,0x3ff00000
	.type	.L_2il0floatpacket.11,@object
	.size	.L_2il0floatpacket.11,8
	.section .rodata.str1.32, "aMS",@progbits,1
	.align 32
	.align 32
.L_2__STRING.0:
	.byte	76
	.byte	111
	.byte	99
	.byte	97
	.byte	108
	.byte	32
	.byte	66
	.byte	87
	.byte	58
	.byte	32
	.byte	37
	.byte	46
	.byte	50
	.byte	108
	.byte	102
	.byte	32
	.byte	71
	.byte	66
	.byte	47
	.byte	115
	.byte	9
	.byte	40
	.byte	37
	.byte	46
	.byte	50
	.byte	108
	.byte	102
	.byte	32
	.byte	77
	.byte	66
	.byte	47
	.byte	115
	.byte	41
	.byte	9
	.byte	76
	.byte	111
	.byte	99
	.byte	97
	.byte	108
	.byte	32
	.byte	65
	.byte	67
	.byte	66
	.byte	66
	.byte	58
	.byte	32
	.byte	37
	.byte	46
	.byte	50
	.byte	108
	.byte	102
	.byte	46
	.byte	32
	.byte	91
	.byte	97
	.byte	105
	.byte	109
	.byte	32
	.byte	119
	.byte	97
	.byte	115
	.byte	32
	.byte	37
	.byte	100
	.byte	93
	.byte	10
	.byte	0
	.type	.L_2__STRING.0,@object
	.size	.L_2__STRING.0,67
	.data
	.section .note.GNU-stack, ""
// -- Begin DWARF2 SEGMENT .eh_frame
	.section .eh_frame,"a",@progbits
.eh_frame_seg:
	.align 8
	.4byte 0x00000014
	.8byte 0x7801000100000000
	.8byte 0x0000019008070c10
	.4byte 0x00000000
	.4byte 0x00000094
	.4byte 0x0000001c
	.8byte ..___tag_value_load.1
	.8byte ..___tag_value_load.32-..___tag_value_load.1
	.byte 0x04
	.4byte ..___tag_value_load.3-..___tag_value_load.1
	.4byte 0x100e028f
	.byte 0x04
	.4byte ..___tag_value_load.5-..___tag_value_load.3
	.4byte 0x180e0383
	.byte 0x04
	.4byte ..___tag_value_load.7-..___tag_value_load.5
	.4byte 0x200e0486
	.byte 0x04
	.4byte ..___tag_value_load.9-..___tag_value_load.7
	.4byte 0x0401f00e
	.4byte ..___tag_value_load.10-..___tag_value_load.9
	.2byte 0x1e8c
	.byte 0x04
	.4byte ..___tag_value_load.11-..___tag_value_load.10
	.2byte 0x1d8d
	.byte 0x04
	.4byte ..___tag_value_load.12-..___tag_value_load.11
	.2byte 0x1c8e
	.byte 0x04
	.4byte ..___tag_value_load.15-..___tag_value_load.12
	.2byte 0x04cc
	.4byte ..___tag_value_load.16-..___tag_value_load.15
	.2byte 0x04cd
	.4byte ..___tag_value_load.17-..___tag_value_load.16
	.2byte 0x04ce
	.4byte ..___tag_value_load.18-..___tag_value_load.17
	.4byte 0x04c6200e
	.4byte ..___tag_value_load.20-..___tag_value_load.18
	.4byte 0x04c3180e
	.4byte ..___tag_value_load.22-..___tag_value_load.20
	.4byte 0x04cf100e
	.4byte ..___tag_value_load.24-..___tag_value_load.22
	.2byte 0x080e
	.byte 0x04
	.4byte ..___tag_value_load.25-..___tag_value_load.24
	.8byte 0x8c0486038301f00e
	.8byte 0x00028f1c8e1d8d1e
	.2byte 0x0000
# End
